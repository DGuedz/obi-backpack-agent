import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

def analyze_crash():
    print("\n [CRASH ANALYSIS] Investigating BTC Drop...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    SYMBOL = "BTC_USDC_PERP"
    
    # 1. Get Technical Context (4h and 1h)
    print("    Scanning Market Structure...")
    try:
        # 4H for Major Support
        k_4h = data.get_klines(SYMBOL, "4h", limit=100)
        df_4h = pd.DataFrame(k_4h)
        df_4h = df_4h.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
        df_4h['close'] = df_4h['close'].astype(float)
        
        ema_200_4h = df_4h['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        support_4h = df_4h['low'].min() # Recent low
        
        # 1H for Immediate Momentum
        k_1h = data.get_klines(SYMBOL, "1h", limit=100)
        df_1h = pd.DataFrame(k_1h)
        df_1h = df_1h.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
        df_1h['close'] = df_1h['close'].astype(float)
        
        rsi_1h = indicators.calculate_rsi(df_1h).iloc[-1]
        current_price = df_1h['close'].iloc[-1]
        
        print(f"    Current Price: ${current_price:,.2f}")
        print(f"    RSI (1h): {rsi_1h:.2f} {'(OVERSOLD - Bounce Likely)' if rsi_1h < 30 else ''}")
        print(f"    Major Support (4h EMA 200): ${ema_200_4h:,.2f}")
        
        # 2. Check Order Book Walls (Where are the buyers?)
        print("    Checking Order Book Depth...")
        depth = data.get_depth(SYMBOL)
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # Find biggest bid wall below price
        max_bid_vol = 0
        wall_price = 0
        
        # Analyze top 50 levels
        for bid in bids[:50]:
            p = float(bid[0])
            q = float(bid[1])
            if q > max_bid_vol:
                max_bid_vol = q
                wall_price = p
                
        print(f"   ️ BUY WALL DETECTED: {max_bid_vol:.4f} BTC @ ${wall_price:,.2f}")
        
        dist_to_wall = ((current_price - wall_price) / current_price) * 100
        print(f"   -> Distance to Support: {dist_to_wall:.2f}%")
        
        if current_price < ema_200_4h:
            print("   ️ WARNING: Price is below 4H EMA 200 (Bearish Trend Shift).")
        else:
            print("    Price is still above Major Trend (4H EMA 200).")

    except Exception as e:
        print(f"    Analysis Error: {e}")

if __name__ == "__main__":
    analyze_crash()
