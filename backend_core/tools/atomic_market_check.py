import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE')) # Necessário para backpack_data

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Setup simples de log
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("AtomicCheck")

async def atomic_scan():
    load_dotenv()
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    symbols = ["BTC_USDC_PERP", "SOL_USDC_PERP", "SUI_USDC_PERP", "SEI_USDC_PERP", "ETH_USDC_PERP"]
    
    print("\n ANÁLISE ATÔMICA DE MERCADO (BULLISH HYPOTHESIS)\n")
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI':<6} | {'SPREAD %':<8} | {'VERDICT'}")
    print("-" * 65)
    
    bullish_score = 0
    
    for symbol in symbols:
        try:
            # 1. Depth & OBI
            depth = data_client.get_orderbook_depth(symbol)
            if not depth: continue
            
            obi = oracle.calculate_obi(depth)
            
            # 2. Price & Spread
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            mid_price = (best_bid + best_ask) / 2
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            
            # 3. Veredito Atômico
            verdict = "NEUTRAL"
            if obi > 0.2: 
                verdict = "🟢 BULL"
                bullish_score += 1
            elif obi < -0.2: 
                verdict = " BEAR"
                bullish_score -= 1
            
            # Imprimir linha
            print(f"{symbol:<15} | {mid_price:<10.4f} | {obi:>5.2f} | {spread_pct:>7.4f}% | {verdict}")
            
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
            
    print("-" * 65)
    
    # Conclusão
    if bullish_score > 1:
        print("\n CONFIRMADO: Estrutura de Mercado BULLISH.")
        print("   -> Recomendação: Ativar Volume Farmer com flag '--long'.")
    elif bullish_score < -1:
        print("\n DIVERGÊNCIA: Dados indicam pressão BEARISH.")
        print("   -> Recomendação: Cautela. Manter modo 'auto' ou aguardar.")
    else:
        print("\n️ MISTO/NEUTRO: Sem direção clara nos books.")
        print("   -> Recomendação: Modo 'auto' (Straddle) é mais seguro.")

if __name__ == "__main__":
    asyncio.run(atomic_scan())
