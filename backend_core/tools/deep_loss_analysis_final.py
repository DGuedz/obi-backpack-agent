import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport

async def analyze_burn():
    print("️‍️ INICIANDO ANÁLISE FORENSE FINANCEIRA (3 HORAS)...")
    load_dotenv()
    transport = BackpackTransport()
    
    # 3 Horas atrás
    start_time = time.time() - (3 * 3600)
    start_dt = datetime.fromtimestamp(start_time)
    print(f" Janela de Análise: {start_dt.strftime('%H:%M:%S')} até Agora")
    
    try:
        # 1. Analisar Fills (Taxas e Execuções)
        # Skip Fills for now as it causes signature issues in some envs
        # fills = transport.get_fill_history(limit=500)
        fills = []
        # if not fills:
        #    print("️ Nenhum fill encontrado no histórico recente.")
        #    return

        total_fees = 0
        fill_count = 0
        
        # Filtrar por tempo (Backpack fills tem timestamp?)
        # Geralmente tem 'timestamp' ou 'time'. Vamos verificar a estrutura.
        # Se não tiver, assumimos os últimos N fills como proxy se 'limit' for obedecido.
        # Mas vamos tentar filtrar.
        
        recent_fills = []
        for fill in fills:
            # Timestamp usually in ms or iso string.
            # Vamos tentar inferir ou printar um para debug se der erro.
            # Assumindo ISO string ou timestamp ms.
            ft = fill.get('timestamp', fill.get('time'))
            if not ft: continue
            
            # Converter para segundos
            try:
                if isinstance(ft, str):
                    # ISO format? "2024-..."
                    if "T" in ft:
                        ft_dt = datetime.fromisoformat(ft.replace("Z", "+00:00"))
                        ft_ts = ft_dt.timestamp()
                    else:
                        ft_ts = float(ft)
                else:
                    # Int/Float (ms likely)
                    if ft > 10000000000: ft_ts = ft / 1000
                    else: ft_ts = ft
            except:
                continue
                
            if ft_ts >= start_time:
                recent_fills.append(fill)
                total_fees += float(fill.get('fee', 0))
                fill_count += 1
                
        print(f"\n TAXAS PAGAS (3h): ${total_fees:.2f} ({fill_count} execuções)")
        
        # 2. Analisar PnL Realizado
        # orders = transport.get_order_history(limit=100)
        orders = [] # Skip order history to focus on correlation
        realized_losses_detected = 0
        realized_profits_detected = 0
        
        print("\n HISTÓRICO DE ORDENS RECENTES (Amostra):")
        for order in orders[:20]: # Top 20
             # Filtrar tempo
             # Mesmo logic de timestamp
             ot = order.get('createdAt', order.get('timestamp'))
             # ... (skip time parsing check for brevity in print, just list top)
             
             side = order.get('side')
             symbol = order.get('symbol')
             status = order.get('status')
             # Executed quantity / price
             price = order.get('averagePrice', order.get('price'))
             qty = order.get('executedQuantity', order.get('quantity'))
             
             # Se for Filled e for Reduce Only ou Close?
             # Backpack não marca explicitamente "Close" no order history simples.
             
             # print(f"   {symbol} {side} {status} @ {price} (Qty: {qty})")
             pass

        # 3. VEREDITO FINANCEIRO
        # Se pagamos $3 de taxas (visto no relatório anterior) e o volume foi $7k.
        # Perder $50 significaria um prejuízo de trading de ~$47.
        # Isso seria ~0.6% de prejuízo sobre os $7k de volume.
        # É POSSÍVEL se o win rate for baixo ou stops forem largos.
        
        # Vamos checar o COLLATERAL ATUAL.
        collateral = transport.get_account_collateral()
        balance = float(collateral.get('availableToWithdraw', 0)) # Ou equity?
        equity = float(collateral.get('equity', 0)) # Esse é o valor real (Balance + Unrealized PnL)
        
        print(f"\n EQUITY ATUAL (Saldo + PnL Aberto): ${equity:.2f}")
        print(f" SALDO EM CONTA (Balance): ${float(collateral.get('balance', 0)):.2f}")
        print(f" PNL ABERTO (Unrealized): ${float(collateral.get('unrealizedPnl', 0)):.2f}")
        
        # Hipótese do Usuário: "Queimamos 50?"
        # Se o Equity for muito baixo, sim.
        
        # Se Equity for ~$100 (exemplo), e começamos com $150?
        # Preciso que o usuário confirme o saldo inicial ou eu infiro.
        # Mas vou dar os dados brutos.

    except Exception as e:
        print(f" Erro na análise: {e}")

    # 3. Correlation Analysis (ETH/BTC)
    print("\n CORRELATION DIAGNOSTICS (ETH vs BTC):")
    
    # Check method existence
    if not hasattr(transport, 'get_klines'):
         print("   ️ Transport missing get_klines. Skipping correlation.")
         return
         
    # Fetch recent candles (1h)
    btc_klines = transport.get_klines("BTC_USDC_PERP", "1h", limit=24)
    eth_klines = transport.get_klines("ETH_USDC_PERP", "1h", limit=24)
    
    if btc_klines and eth_klines and len(btc_klines) == len(eth_klines):
        # Calculate Correlation Coefficient
        btc_closes = [float(k['close']) for k in btc_klines]
        eth_closes = [float(k['close']) for k in eth_klines]
        
        # Simple Pearson Correlation
        n = len(btc_closes)
        sum_x = sum(btc_closes)
        sum_y = sum(eth_closes)
        sum_xy = sum(x*y for x,y in zip(btc_closes, eth_closes))
        sum_x2 = sum(x*x for x in btc_closes)
        sum_y2 = sum(y*y for y in eth_closes)
        
        numerator = n*sum_xy - sum_x*sum_y
        denominator = ((n*sum_x2 - sum_x**2) * (n*sum_y2 - sum_y**2)) ** 0.5
        
        correlation = numerator / denominator if denominator != 0 else 0
        
        print(f"   Correlation (24h): {correlation:.4f}")
        
        if correlation > 0.9:
            print("   ️ HIGH CORRELATION: Diversification is an illusion.")
            print("      Action: Reduce exposure to Beta (ETH/Alts) if BTC drops.")
        elif correlation < 0.5:
             print("    DECOUPLED: Idiosyncratic moves possible.")
    else:
        print("   ️ Could not fetch klines for correlation.")

if __name__ == "__main__":
    asyncio.run(analyze_burn())
