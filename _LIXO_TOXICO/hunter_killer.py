import time
import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators
from smart_entry import SmartEntrySniper

# --- CONFIG ---
CHECK_INTERVAL = 60 # Check every 60 seconds
TARGETS = [
    "SOL_USDC_PERP", 
    "ETH_USDC_PERP", 
    "SUI_USDC_PERP", 
    "BNB_USDC_PERP", 
    "HYPE_USDC_PERP", 
    "ZEC_USDC_PERP",
    "JUP_USDC_PERP"
]

def hunter_loop():
    print("\n [HUNTER KILLER] ACTIVATED. Scanning Targets...")
    print(f"    Targets: {TARGETS}")
    print("    Authorized for Lethal Shot (Entry)")
    
    # Init Modules
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    # Create Sniper Instances
    snipers = {}
    for symbol in TARGETS:
        snipers[symbol] = SmartEntrySniper(symbol, data, trade, indicators)

    while True:
        try:
            print(f"\nScanning Cycle at {time.strftime('%H:%M:%S')}...")
            
            # 1. Check if we can open new positions
            try:
                positions = data.get_positions()
                if len(positions) >= 3:
                    print(f"   ️ Max Positions Reached ({len(positions)}/3). Holding Fire.")
                    time.sleep(CHECK_INTERVAL)
                    continue
            except Exception as e:
                print(f"   ️ Error checking positions: {e}")
                
            # 2. Scan Each Target
            for symbol in TARGETS:
                try:
                    snipers[symbol].execute_sniper() # Silent unless signal
                except Exception as e:
                    print(f"    Error scanning {symbol}: {e}")
                    
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n Hunter Killer Stopped by User.")
            break
        except Exception as e:
            print(f"️ Critical Loop Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    hunter_loop()
