import os
import sys
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append("/Users/doublegreen/backpacktrading")
sys.path.append("/Users/doublegreen/backpacktrading/core")

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

def calculate_obi_simple(depth):
    if not depth or 'bids' not in depth or 'asks' not in depth:
        return 0.0
    
    bids = depth.get('bids', [])
    asks = depth.get('asks', [])
    
    if not bids or not asks: return 0.0
    
    # L5 Analysis
    top5_bids = bids[-5:]
    top5_asks = asks[:5]
    
    bid_vol = sum([float(x[1]) for x in top5_bids])
    ask_vol = sum([float(x[1]) for x in top5_asks])
    
    total = bid_vol + ask_vol
    if total == 0: return 0.0
    
    return (bid_vol - ask_vol) / total

def analyze():
    load_dotenv()
    
    try:
        auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        data = BackpackData(auth)
        transport = BackpackTransport()
    except Exception as e:
        print(f"Auth Error: {e}")
        return

    targets = ["HYPE_USDC_PERP", "TRUMP_USDC_PERP", "HYPE_USDC", "TRUMP_USDC"]
    
    print("\n ANÁLISE DE MERCADOS DE PREDIÇÃO (PROXY)")
    print("=" * 70)
    print(f"{'ATIVO':<18} | {'PREÇO':<10} | {'OBI (5LVL)':<10} | {'PAREDE':<15} | {'STATUS'}")
    print("-" * 70)
    
    for symbol in targets:
        try:
            ticker = transport.get_ticker(symbol)
            if not ticker: continue
            
            price = float(ticker['lastPrice'])
            depth = data.get_orderbook_depth(symbol)
            
            obi = calculate_obi_simple(depth)
            
            # Wall Logic
            bids = depth['bids'][-5:]
            asks = depth['asks'][:5]
            bid_vol = sum([float(x[1]) for x in bids])
            ask_vol = sum([float(x[1]) for x in asks])
            
            wall = "-"
            if ask_vol > 0 and bid_vol / ask_vol > 2.0: wall = "🟢 BID WALL"
            elif bid_vol > 0 and ask_vol / bid_vol > 2.0: wall = " ASK WALL"
            
            status = "NEUTRO"
            if obi > 0.3: status = "BULLISH "
            elif obi < -0.3: status = "BEARISH "
            
            print(f"{symbol:<18} | ${price:<10.4f} | {obi:<10.2f} | {wall:<15} | {status}")
            
        except Exception as e:
            # print(f"{symbol:<18} | ERRO: {e}")
            pass
            
    print("-" * 70)
    print("NOTA: OBI positivo indica pressão de compra. Parede indica suporte/resistência.")

if __name__ == "__main__":
    analyze()
