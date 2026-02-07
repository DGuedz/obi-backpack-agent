import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

def analyze_onchain_proxy():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    symbol = "BTC_USDC" # Checking Spot/Perp Proxy
    
    print(f"\n ANALISE ON-CHAIN PROXY (ORDER BOOK & FUNDING) - {symbol}")
    print("==================================================")
    
    # 1. Market Depth (Whale Walls)
    try:
        depth = data.get_depth(symbol)
        if depth:
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            
            # Analyze Top 20 levels
            bid_vol_top20 = sum([float(b[1]) for b in bids[:20]])
            ask_vol_top20 = sum([float(a[1]) for a in asks[:20]])
            
            ratio = bid_vol_top20 / ask_vol_top20 if ask_vol_top20 > 0 else 0
            
            print(f" ORDER FLOW IMBALANCE (Top 20 Levels):")
            print(f"   🟢 BID Support: {bid_vol_top20:.4f} BTC")
            print(f"    ASK Pressure: {ask_vol_top20:.4f} BTC")
            print(f"   ️  Ratio: {ratio:.2f}x ({'BULLISH' if ratio > 1.2 else 'BEARISH' if ratio < 0.8 else 'NEUTRAL'})")
            
            # Find Whale Walls (> 1 BTC)
            print(f"\n WHALE WALLS (Visible Support/Resistance):")
            for p, q in bids:
                if float(q) > 1.0:
                    print(f"   ️  SUPPORT: {p} ({q} BTC)")
            for p, q in asks:
                if float(q) > 1.0:
                    print(f"    RESISTANCE: {p} ({q} BTC)")
                    
    except Exception as e:
        print(f"    Error fetching depth: {e}")

    # 2. Ticker Data (Funding & Volume)
    try:
        ticker = data.get_ticker(symbol)
        if ticker:
            last_price = float(ticker.get('lastPrice', 0))
            price_change = float(ticker.get('priceChangePercent', 0))
            volume = float(ticker.get('volume', 0))
            
            print(f"\n MARKET STATUS:")
            print(f"    Price: ${last_price:,.2f} ({price_change}%)")
            print(f"    Volume 24h: {volume:,.2f}")
            
            # Note: Funding rate usually comes from a specific endpoint or field, checking ticker generic
            # Backpack API ticker might not have funding, assuming standard spot/perp logic
            
    except Exception as e:
        print(f"    Error fetching ticker: {e}")
        
    print("==================================================")

if __name__ == "__main__":
    analyze_onchain_proxy()
