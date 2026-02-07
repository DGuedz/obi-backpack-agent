import time
import os
import sys
from dotenv import load_dotenv

# Core Modules
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# Protocol Omega Modules
from sentinel import Sentinel
from weaver_grid import WeaverGrid
from smart_entry import SmartEntrySniper

# Config
SYMBOL = "BTC_USDC_PERP" # Can be dynamic or list
ATR_THRESHOLD = 500.0 # Volatility Switch Threshold (To be tuned)

def run_orchestrator():
    print("\n [ORCHESTRATOR] Initializing PROTOCOL OMEGA...")
    
    # 1. Connect
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    # 2. Activate Sentinel (Threaded Shield)
    sentinel = Sentinel(data, trade)
    sentinel.start()
    
    # 3. Initialize Strategies
    weaver = WeaverGrid(SYMBOL, data, trade, indicators)
    sniper = SmartEntrySniper(SYMBOL, data, trade, indicators)
    
    print("    Systems Online. Entering Loop...")
    
    try:
        while True:
            # 4. Volatility Check (ATR)
            # Need fresh data for ATR check
            # For simplicity, let Weaver calculate and return, or fetch here
            # Fetching small batch for quick check
            try:
                candles = data.get_klines(SYMBOL, "1h", limit=20)
                if candles:
                    import pandas as pd
                    df = pd.DataFrame(candles)
                    df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
                    df['close'] = df['close'].astype(float)
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    
                    atr = indicators.calculate_atr(df, window=14).iloc[-1]
                    
                    print(f"\n [MARKET STATE] ATR: {atr:.2f}")
                    
                    if atr < ATR_THRESHOLD:
                        # Low Volatility -> Grid Mode (Weaver)
                        print("    Low Volatility Detected -> Active Strategy: WEAVER GRID")
                        weaver.execute_grid()
                    else:
                        # High Volatility -> Sniper Mode (Smart Entry)
                        print("    High Volatility Detected -> Active Strategy: SNIPER")
                        sniper.execute_sniper()
                        
            except Exception as e:
                print(f"   ️ Orchestrator Loop Error: {e}")
            
            time.sleep(60) # Main Loop Pulse
            
    except KeyboardInterrupt:
        print("\n Shutdown Requested.")
        sentinel.stop()
        sys.exit(0)

if __name__ == "__main__":
    run_orchestrator()
