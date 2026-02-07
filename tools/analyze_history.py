import os
import sys
import asyncio
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

async def analyze_history():
    load_dotenv()
    print("\n ANALISANDO ÚLTIMAS 30 OPERAÇÕES...")
    
    transport = BackpackTransport()
    
    # Buscar histórico (Tentar Orders e Fills)
    print("1. Buscando Histórico de Ordens...")
    orders = transport.get_order_history(limit=100)
    
    if not orders:
        print(" Histórico de Ordens vazio ou erro. Tentando Fills...")
        fills = transport.get_fill_history(limit=100)
        
        if not fills:
            print(" Falha ao obter dados (Orders e Fills).")
            return
        else:
            print(f" {len(fills)} Fills recuperados via /wapi.")
            data_source = fills
            mode = "fills"
    else:
        print(f" {len(orders)} Ordens recuperadas.")
        data_source = orders
        mode = "orders"

    # Processar dados
    data = []
    
    if mode == "fills":
        # Debug: Print first fill to check structure
        if len(data_source) > 0:
            print(f"DEBUG Fill Sample: {data_source[0]}")
            
        for fill in data_source:
             ts = fill.get('timestamp', 0)
             if isinstance(ts, str):
                 # Can be ISO format or string int
                 if ts.isdigit():
                     ts = int(ts)
                 else:
                     # Try parsing ISO
                     try:
                         dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                         ts = dt.timestamp() * 1000
                     except:
                         ts = 0
             
             entry = {
                'time': datetime.fromtimestamp(ts / 1000 if ts > 10000000000 else ts),
                'symbol': fill.get('symbol'),
                'side': fill.get('side'),
                'price': float(fill.get('price', 0)),
                'quantity': float(fill.get('quantity', 0)),
                'fee': float(fill.get('fee', 0)),
                'isMaker': fill.get('isMaker'),
                'pnl': float(fill.get('realizedPnl', 0)) if 'realizedPnl' in fill else 0.0
            }
             data.append(entry)
             
    elif mode == "orders":
        # Estrutura de ordem pode ter executedQuantity, price, status
        # Só interessa filled
        for order in data_source:
            if order.get('status') == 'Filled' or float(order.get('executedQuantity', 0)) > 0:
                 # Orders endpoint might not have PnL directly?
                 # Often it does if it's a reduceOnly fill.
                 # Let's check fields.
                 
                 entry = {
                    'time': datetime.fromtimestamp(order.get('createdAt', 0) / 1000 if order.get('createdAt') > 10000000000 else order.get('createdAt', 0)),
                    'symbol': order.get('symbol'),
                    'side': order.get('side'),
                    'price': float(order.get('avgPrice', order.get('price', 0)) or 0), # avgPrice is better for filled
                    'quantity': float(order.get('executedQuantity', 0)),
                    'fee': float(order.get('fee', 0)), # Sometimes fee is not in order object
                    'isMaker': order.get('postOnly', False), # Approximation
                    'pnl': 0.0 # Orders API usually doesn't have PnL. Fills API is better.
                }
                 data.append(entry)
        
        if not data:
             print("️ Nenhuma ordem preenchida encontrada.")
             return
             
    df = pd.DataFrame(data)
    df.sort_values('time', inplace=True)
    
    # ... (timestamp fix was applied previously)
    
    # 2. Reconstruir PnL via FIFO Matching
    print("\n Reconstruindo PnL via FIFO Matching...")
    
    trades_analysis = []
    
    # Agrupar por símbolo
    fills_by_symbol = {}
    for entry in data:
        sym = entry['symbol']
        if sym not in fills_by_symbol:
            fills_by_symbol[sym] = []
        fills_by_symbol[sym].append(entry)
        
    for sym, fills in fills_by_symbol.items():
        # Sort by time
        fills.sort(key=lambda x: x['time'])
        
        inventory = [] # List of {'price': p, 'qty': q, 'side': 'Buy'/'Sell'}
        
        for fill in fills:
            qty = fill['quantity']
            price = fill['price']
            side = fill['side']
            fee = fill['fee']
            is_maker = fill['isMaker']
            
            # Determinar se é Abertura ou Fechamento
            # Simplificação: Se inventory vazio, é abertura.
            # Se side diferente do inventory[0], é fechamento.
            
            remaining_qty = qty
            
            while remaining_qty > 0:
                if not inventory:
                    # Nova posição
                    inventory.append({'price': price, 'qty': remaining_qty, 'side': side})
                    remaining_qty = 0
                else:
                    head = inventory[0]
                    if head['side'] != side:
                        # Fechamento (Match)
                        match_qty = min(remaining_qty, head['qty'])
                        
                        # Calc PnL
                        # Long: Buy @ Entry, Sell @ Exit -> (Exit - Entry) * Qty
                        # Short: Sell @ Entry, Buy @ Exit -> (Entry - Exit) * Qty
                        
                        if head['side'] == 'Buy': # Long Close
                            raw_pnl = (price - head['price']) * match_qty
                            trade_type = 'Long'
                        else: # Short Close
                            raw_pnl = (head['price'] - price) * match_qty
                            trade_type = 'Short'
                            
                        # Registrar Trade
                        trades_analysis.append({
                            'time': fill['time'],
                            'symbol': sym,
                            'type': trade_type,
                            'entry_price': head['price'],
                            'exit_price': price,
                            'quantity': match_qty,
                            'raw_pnl': raw_pnl,
                            'fee': fee * (match_qty / qty), # Proporcional fee
                            'is_maker_entry': False, # Lost info
                            'is_maker_exit': is_maker
                        })
                        
                        # Update Inventory
                        head['qty'] -= match_qty
                        remaining_qty -= match_qty
                        
                        if head['qty'] < 0.0000001:
                            inventory.pop(0)
                    else:
                        # Aumento de posição (mesmo lado)
                        inventory.append({'price': price, 'qty': remaining_qty, 'side': side})
                        remaining_qty = 0

    # Converter análise para DataFrame
    df_trades = pd.DataFrame(trades_analysis)
    
    if df_trades.empty:
        print("️ Não foi possível reconstruir trades fechados (apenas posições abertas?).")
        return

    # Calcular Net PnL
    df_trades['net_pnl'] = df_trades['raw_pnl'] - df_trades['fee']
    
    total_pnl = df_trades['net_pnl'].sum()
    total_fees = df_trades['fee'].sum()
    
    print("\n RELATÓRIO DE PERFORMANCE (RECONSTRUÍDO)")
    print(f"Total Trades:        {len(df_trades)}")
    print(f"Total PnL Líquido:   ${total_pnl:.2f}")
    print(f"Total Taxas:         ${total_fees:.2f}")
    
    wins = df_trades[df_trades['net_pnl'] > 0]
    losses = df_trades[df_trades['net_pnl'] <= 0]
    
    win_rate = (len(wins) / len(df_trades)) * 100
    print(f"\n Win Rate: {win_rate:.1f}% ({len(wins)} Wins / {len(losses)} Losses)")
    
    if not wins.empty:
        print(f" Média Win: ${wins['net_pnl'].mean():.2f}")
    if not losses.empty:
        print(f" Média Loss: ${losses['net_pnl'].mean():.2f}")

    print("\n DETALHE DAS PERDAS:")
    for idx, row in losses.tail(10).iterrows():
        print(f"   {row['time']} | {row['symbol']} ({row['type']}) | PnL: ${row['net_pnl']:.2f} | Entry: {row['entry_price']} -> Exit: {row['exit_price']}")

    # Análise de Erros
    print("\n️ DIAGNÓSTICO DE ERROS:")
    
    # 1. Fees Impact
    gross_pnl = df_trades['raw_pnl'].sum()
    if gross_pnl > 0 and total_fees > (gross_pnl * 0.3):
        print(f"️ ALERTA CRÍTICO: Taxas consumiram {total_fees/gross_pnl*100:.1f}% do lucro bruto!")
        print("   -> AÇÃO: Usar PostOnly (Maker) é OBRIGATÓRIO.")
        
    # 2. Stop Loss Analysis
    # Se a perda média for muito maior que o ganho médio
    if not wins.empty and not losses.empty:
        avg_win = wins['net_pnl'].mean()
        avg_loss = abs(losses['net_pnl'].mean())
        if avg_loss > avg_win:
            print(f"️ ALERTA: Perda média (${avg_loss:.2f}) > Ganho médio (${avg_win:.2f}).")
            print("   -> AÇÃO: Apertar Stop Loss ou melhorar Risco/Retorno.")

    # 3. Leverage Check (Simulado)
    # Se perdemos muito rápido (variação de preço pequena causou grande perda)
    for idx, row in losses.iterrows():
        price_delta_pct = abs(row['exit_price'] - row['entry_price']) / row['entry_price']
        if price_delta_pct < 0.01 and abs(row['net_pnl']) > 5:
            print(f"️ ALERTA: Perda alta (${row['net_pnl']:.2f}) com movimento pequeno ({price_delta_pct*100:.2f}%).")
            print("   -> DIAGNÓSTICO: Alavancagem muito alta para o stop curto.")
            
    print("\n️ RECOMENDAÇÕES DE AJUSTE:")
    print("1. Ajustar 'manual_entry.py' e 'sniper_executor.py' para forçar PostOnly.")
    print("2. Recalcular SL baseado em ATR (Volatilidade) e não % fixo se estiver sendo violinado.")


if __name__ == "__main__":
    asyncio.run(analyze_history())
