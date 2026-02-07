import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

async def run_diagnostics():
    print(" INICIANDO DIAGNÓSTICO DE PRECISÃO (LIVRO & EXECUÇÃO)...")
    load_dotenv()
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    symbol = "DOGE_USDC_PERP" # Ativo de teste barato
    
    # 1. ANÁLISE DO LIVRO (MICROESTRUTURA)
    print(f"\n ANÁLISE DE LIVRO: {symbol}")
    depth = data.get_orderbook_depth(symbol)
    
    if depth:
        bids = depth['bids']
        asks = depth['asks']
        
        best_bid = float(bids[-1][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100
        
        print(f"   Best Bid: {best_bid}")
        print(f"   Best Ask: {best_ask}")
        print(f"   Spread: {spread:.6f} ({spread_pct:.4f}%)")
        
        # OBI
        obi = oracle.calculate_obi(depth)
        print(f"   OBI (Fluxo): {obi:.2f}")
        
        # Liquidity Walls
        bid_vol_top5 = sum([float(x[1]) for x in bids[-5:]])
        ask_vol_top5 = sum([float(x[1]) for x in asks[:5]])
        
        print(f"   Bid Vol (Top 5): {bid_vol_top5:.0f}")
        print(f"   Ask Vol (Top 5): {ask_vol_top5:.0f}")
        
        ratio = bid_vol_top5 / ask_vol_top5 if ask_vol_top5 > 0 else 0
        print(f"   Imbalance Ratio: {ratio:.2f}x")
        
    else:
        print(" Falha ao ler livro.")
        return

    # 2. TESTE DE EXECUÇÃO (TP/SL)
    print("\n️ TESTE DE VALIDACAO DE TP/SL (Protocolo TriggerMarket)")
    
    # Vamos tentar colocar uma ordem condicional (Stop Buy) longe do preço para não executar
    # Preço atual ~0.11. Trigger Buy @ 0.20.
    
    trigger_price = round(best_ask * 1.5, 5)
    qty = 100 # ~ $11 USD
    
    print(f"   Tentando criar TriggerMarket Buy @ {trigger_price}...")
    
    try:
        # Test 1: Market with triggerPrice
        print("    Tentando 'Market' com triggerPrice...")
        res = transport.execute_order(
            symbol=symbol,
            order_type="Market", 
            side="Buy",
            quantity=qty,
            trigger_price=trigger_price
        )
        
        if res and 'id' in res:
            print(f"    SUCESSO: Market+Trigger aceito! ID: {res['id']}")
            transport.cancel_order(symbol, res['id'])
        else:
            print(f"    FALHA Market+Trigger: {res}")
            
            # Test 2: Limit with triggerPrice (TriggerLimit equivalent?)
            print("    Tentando 'Limit' com triggerPrice...")
            res2 = transport.execute_order(
                symbol=symbol,
                order_type="Limit",
                side="Buy",
                quantity=qty,
                price=str(round(trigger_price * 1.01, 5)), # Limit price slightly above trigger
                trigger_price=trigger_price
            )
            if res2 and 'id' in res2:
                 print(f"    SUCESSO: Limit+Trigger aceito! ID: {res2['id']}")
                 transport.cancel_order(symbol, res2['id'])
            else:
                 print(f"    FALHA Limit+Trigger: {res2}")

    except Exception as e:
        print(f"    ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_diagnostics())
