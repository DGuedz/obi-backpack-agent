import os
import sys
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def analyze_losses():
    print("️ INICIANDO ANÁLISE FORENSE DE PERDAS (S1-S4)...")
    load_dotenv()
    
    transport = BackpackTransport()
    all_fills = []
    limit = 100
    offset = 0
    has_more = True
    
    print(" Baixando histórico completo de trades para reconstruir PnL...")
    
    # Recuperação de dados (paginada)
    while has_more:
        try:
            fills = transport.get_fill_history(limit=limit, offset=offset)
            if not fills or len(fills) == 0:
                has_more = False
                break
            
            all_fills.extend(fills)
            offset += len(fills)
            
            print(f"   ⏳ Processados {len(all_fills)} trades...", end='\r')
            
            if len(fills) < limit:
                has_more = False
                
        except Exception as e:
            print(f" Erro na paginação: {e}")
            break
            
    print(f"\n Total de Trades Analisados: {len(all_fills)}")
    
    if not all_fills:
        return

    # Processamento de Dados
    trades_data = []
    
    for fill in all_fills:
        ts = fill.get('timestamp', 0)
        # Normalizar timestamp
        if isinstance(ts, str):
            if ts.isdigit(): ts = int(ts)
            else:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts = dt.timestamp() * 1000
                except: ts = 0
        
        dt_obj = datetime.fromtimestamp(ts / 1000 if ts > 10000000000 else ts, tz=timezone.utc)
        
        # Extrair PnL (Realized PnL vem no fill de fechamento)
        realized_pnl = float(fill.get('realizedPnl', 0))
        fee = float(fill.get('fee', 0))
        price = float(fill.get('price', 0))
        qty = float(fill.get('quantity', 0))
        symbol = fill.get('symbol')
        side = fill.get('side')
        
        # Considerar apenas trades com PnL realizado (fechamento) ou taxas
        # Se realizedPnl != 0, é um fechamento com lucro/prejuízo
        # Taxas são custos sempre
        
        net_result = realized_pnl - fee
        
        trades_data.append({
            'date': dt_obj,
            'symbol': symbol,
            'side': side,
            'price': price,
            'quantity': qty,
            'volume': price * qty,
            'realized_pnl': realized_pnl,
            'fee': fee,
            'net_result': net_result
        })

    df = pd.DataFrame(trades_data)
    df.sort_values('date', inplace=True)
    
    # --- ANÁLISE DE PERDAS ---
    
    # 1. Total Global
    total_pnl_gross = df['realized_pnl'].sum()
    total_fees = df['fee'].sum()
    total_net = df['net_result'].sum()
    
    # 2. Apenas Perdas (Trades negativos)
    losing_trades = df[df['realized_pnl'] < 0]
    total_loss_gross = losing_trades['realized_pnl'].sum()
    loss_count = len(losing_trades)
    
    # 3. Identificar "Flash Crashes" / Grandes Drawdowns
    # Ordenar por maior prejuízo líquido
    worst_trades = df.sort_values('net_result', ascending=True).head(10)
    
    # 4. Agrupamento por Dia (Para ver dias de fúria/crash)
    df['day'] = df['date'].dt.date
    daily_pnl = df.groupby('day')['net_result'].sum().sort_values()
    worst_days = daily_pnl.head(5)
    
    print("\n RELATÓRIO DE PERDAS E DRAWDOWNS")
    print("=" * 60)
    print(f" Resultado Líquido Total:   ${total_net:,.2f}")
    print(f" Total de Taxas Pagas:      ${total_fees:,.2f}")
    print(f" Soma de Todas as Perdas:   ${total_loss_gross:,.2f} (em {loss_count} trades)")
    print(f" Investimento Estimado:     $1,000.00")
    print(f" Equity Atual (Estimado):   ${1000 + total_net:,.2f}")
    
    print("\n TOP 10 MAIORES PREJUÍZOS (FLASH CRASHES/STOPS)")
    print("=" * 60)
    print(f"{'Data':<20} | {'Symbol':<15} | {'Side':<5} | {'Loss (Liq)':<12} | {'Preço':<10}")
    print("-" * 75)
    
    for _, row in worst_trades.iterrows():
        loss_val = row['net_result']
        price_val = row['price']
        print(f"{row['date'].strftime('%Y-%m-%d %H:%M:%S'):<20} | {row['symbol']:<15} | {row['side']:<5} | ${loss_val:>10.2f} | ${price_val:.4f}")

    print("\n TOP 5 PIORES DIAS (DRAWDOWNS DIÁRIOS)")
    print("=" * 60)
    for day, pnl in worst_days.items():
        print(f"   • {day}: ${pnl:,.2f}")
        
    # Análise de Ativos Tóxicos
    print("\n️ ATIVOS MAIS TÓXICOS (MAIOR PREJUÍZO ACUMULADO)")
    print("=" * 60)
    toxic_assets = df.groupby('symbol')['net_result'].sum().sort_values().head(5)
    for sym, val in toxic_assets.items():
        print(f"   • {sym:<15}: ${val:,.2f}")

    # Conclusão sobre o Depósito de $1k
    print("\n ANÁLISE DO INVESTIMENTO ($1K)")
    print("=" * 60)
    print(f"Depósito Inicial: $1,000.00")
    print(f"Taxas Consumiram: ${total_fees:,.2f} ({(total_fees/1000)*100:.1f}%)")
    print(f"Perdas Trading:   ${abs(total_loss_gross):,.2f} (Soma bruta de perdas)")
    print(f"Lucros Trading:   ${df[df['realized_pnl'] > 0]['realized_pnl'].sum():,.2f}")
    print(f"Saldo Final Real: ${1000 + total_net:,.2f}")

if __name__ == "__main__":
    asyncio.run(analyze_losses())
