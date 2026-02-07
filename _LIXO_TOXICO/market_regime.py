import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

def check_market_regime():
    print("\n [GLOBAL MARKET REGIME] SCANNING CORRELATION...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    try:
        tickers = data.get_tickers()
        if not tickers: return "UNKNOWN"
        
        total_assets = 0
        dropping_assets = 0
        severe_drop_assets = 0 # > 3% drop
        
        print(f"\n   {'SYMBOL':<15} | {'CHANGE 24H':<10} | {'STATUS'}")
        print("-" * 45)
        
        for t in tickers:
            symbol = t['symbol']
            if not symbol.endswith('_PERP'): continue
            
            change = float(t.get('priceChangePercent', 0))
            total_assets += 1
            
            status = "🟢"
            if change < 0:
                dropping_assets += 1
                status = ""
            if change < -3.0:
                severe_drop_assets += 1
                status = ""
                
            # Print top volume ones or significant moves
            quote_vol = float(t.get('quoteVolume', 0))
            if quote_vol > 1_000_000: # Filter noise
                print(f"   {symbol:<15} | {change:>+6.2f}%    | {status}")
                
        bear_ratio = dropping_assets / total_assets if total_assets > 0 else 0
        
        print("-" * 45)
        print(f"    BEAR RATIO: {bear_ratio*100:.1f}% of market is RED.")
        print(f"    CRASH RATIO: {severe_drop_assets} assets down > 3%.")
        
        if bear_ratio > 0.70:
            print("\n    VERDICT: MARKET CRASH (BEAR REGIME).")
            print("    ACTION: LONG FORBIDDEN. SHORT ONLY.")
            return "BEAR"
        elif bear_ratio < 0.30:
            print("\n    VERDICT: BULL RUN (BULL REGIME).")
            print("    ACTION: SHORT FORBIDDEN. LONG ONLY.")
            return "BULL"
        else:
            print("\n   ️ VERDICT: MIXED MARKET (CHOP).")
            return "NEUTRAL"
            
    except Exception as e:
        print(f"    Error: {e}")
        return "UNKNOWN"

if __name__ == "__main__":
    check_market_regime()
