import os
import sys
import pandas as pd

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'obiwork_core'))
sys.path.append(os.path.join(project_root, 'obiwork_core', 'core'))

from obiwork_core.core.backpack_transport import BackpackTransport
from obiwork_core.core.backpack_data import BackpackData
from obiwork_core.core.backpack_auth import BackpackAuth
from obiwork_core.core.technical_oracle import TechnicalOracle
from dotenv import load_dotenv

load_dotenv()

def test_trend():
    print(" Testando Oráculo de Tendência (Ironclad Logic)...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    symbols = ['BTC_USDC_PERP', 'SOL_USDC_PERP']
    
    for s in symbols:
        print(f"\n Analisando {s}...")
        try:
            # 1. Trend Bias (1m)
            trend_1m = oracle.get_trend_bias(s, "1m", ema_period=50)
            
            # 2. Get Price and EMA for debug
            klines = data.get_klines(s, "1m", limit=60)
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            price = df.iloc[-1]['close']
            ema = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            print(f"   Preço: {price:.2f}")
            print(f"   EMA(50): {ema:.2f}")
            print(f"   Viés (1m): {trend_1m}")
            
            if trend_1m == "BULLISH":
                print("    PERMISSÃO: Apenas LONG")
            elif trend_1m == "BEARISH":
                print("    PERMISSÃO: Apenas SHORT")
            else:
                print("   ️ PERMISSÃO: Neutro (Cuidado)")
                
        except Exception as e:
            print(f"    Erro: {e}")

if __name__ == "__main__":
    test_trend()
