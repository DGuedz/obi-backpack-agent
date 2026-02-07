
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
indicators = BackpackIndicators()

def analyze_candidates():
    print(" PRE-SET FILTER: Analyzing Candidates for Positioning...")
    print("=========================================================")
    
    # Candidates from Radar (Top Volatility/Volume)
    # Based on previous radar output: IP, MET, PAXG, FOGO, TIA, APT
    candidates = ["IP_USDC_PERP", "MET_USDC_PERP", "PAXG_USDC_PERP", "FOGO_USDC_PERP", "TIA_USDC_PERP"]
    
    valid_setups = []
    
    for symbol in candidates:
        try:
            # Fetch Data
            klines = data.get_klines(symbol, interval="15m", limit=50)
            if not klines: continue
            
            df = pd.DataFrame(klines)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            # Indicators
            rsi = indicators.calculate_rsi(df).iloc[-1]
            bb = indicators.calculate_bollinger_bands(df)
            price = df['close'].iloc[-1]
            upper = bb['upper'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            
            # Trend Check (SMA 20)
            sma = bb['middle'].iloc[-1]
            trend = "BULL" if price > sma else "BEAR"
            
            # Pre-Set Criteria
            # 1. Volatility check (BB Width)
            bb_width = (upper - lower) / sma
            volatility = "HIGH" if bb_width > 0.05 else "LOW"
            
            # 2. Setup Match
            setup = "NONE"
            if rsi < 35 and trend == "BULL": # Pullback in Uptrend (Golden)
                setup = "LONG (Pullback)"
            elif rsi > 65 and trend == "BEAR": # Rally in Downtrend (Short)
                setup = "SHORT (Trend)"
            elif rsi < 30: # Deep Value
                setup = "LONG (Reversal)"
            elif rsi > 70: # Overextended
                setup = "SHORT (Top)"
                
            print(f"    {symbol}: {price:.4f} | RSI {rsi:.1f} | Trend {trend} | Vol {volatility}")
            
            if setup != "NONE" and volatility == "HIGH":
                print(f"       MATCH: {setup}")
                valid_setups.append((symbol, setup, rsi))
            else:
                print(f"       Skip: No clear setup or low volatility.")
                
        except Exception as e:
            print(f"   ️ Error analyzing {symbol}: {e}")
            
    print("\n TOP PICKS (Ready to Position):")
    if valid_setups:
        for s, setup, r in valid_setups:
            print(f"    {s} -> {setup} (RSI: {r:.1f})")
    else:
        print("    No assets match the Pre-Set right now. Patience.")

if __name__ == "__main__":
    analyze_candidates()
