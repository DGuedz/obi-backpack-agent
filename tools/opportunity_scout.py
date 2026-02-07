import asyncio
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.technical_oracle import TechnicalOracle

async def opportunity_scout():
    print(" SCOUT AGENT: MONITORANDO OPORTUNIDADES (RR 1:4 & ASSIMETRIA)...")
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    # Lista de Vigilância (Top Volatility & Liquidity)
    watchlist = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
        "DOGE_USDC_PERP", "XRP_USDC_PERP", "APT_USDC_PERP",
        "SUI_USDC_PERP", "HYPE_USDC_PERP", "FOGO_USDC_PERP",
        "AVAX_USDC_PERP", "BNB_USDC_PERP", "PEPE_USDC_PERP"
    ]
    
    print(f"{'ATIVO':<10} | {'OBI':<6} | {'IMBALANCE':<10} | {'STATUS':<15} | {'ALVO (RR 1:4)'}")
    print("-" * 75)
    
    while True:
        # Limpar console (opcional, mas melhor logar stream)
        # print("\033[H\033[J") 
        
        found_opportunity = False
        
        for symbol in watchlist:
            try:
                depth = data.get_orderbook_depth(symbol)
                if not depth: continue
                
                obi = oracle.calculate_obi(depth)
                
                # Imbalance Ratio
                bids = depth['bids']
                asks = depth['asks']
                bid_vol = sum([float(x[1]) for x in bids[:5]])
                ask_vol = sum([float(x[1]) for x in asks[:5]])
                ratio = bid_vol / ask_vol if ask_vol > 0 else 0
                
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                price = (best_bid + best_ask) / 2
                
                # Filtro de Assimetria Real
                # Bullish: OBI > 0.3 AND Ratio > 2.0 (Muita pressão de compra)
                # Bearish: OBI < -0.3 AND Ratio < 0.5 (Muita pressão de venda)
                
                signal = None
                
                if obi > 0.3 and ratio > 2.0:
                    signal = "🟢 LONG"
                    entry = best_bid
                    tp = entry * 1.02 # +2%
                    sl = entry * 0.995 # -0.5%
                elif obi < -0.3 and ratio < 0.5:
                    signal = " SHORT"
                    entry = best_ask
                    tp = entry * 0.98 # -2%
                    sl = entry * 1.005 # +0.5%
                    
                if signal:
                    found_opportunity = True
                    print(f"{symbol:<10} | {obi:>6.2f} | {ratio:>5.2f}x     | {signal:<15} | TP: {tp:.4f}")
                    
            except Exception as e:
                pass
                
        if not found_opportunity:
            # Heartbeat para saber que está vivo
            # print(".", end="", flush=True)
            pass
            
        await asyncio.sleep(2) # Scan interval

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(opportunity_scout())
