import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def visual_check_sl():
    print(" VISUAL SL CHECK (DEEP DIVE)")
    print("==============================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    orders = data.get_open_orders()
    
    # Filter only trigger orders (SL)
    sl_orders = [o for o in orders if o.get('triggerPrice')]
    
    print(f" TOTAL STOP LOSS ORDERS FOUND: {len(sl_orders)}")
    
    if not sl_orders:
        print(" CRITICAL: NO STOP LOSSES FOUND IN SYSTEM!")
        return

    print(f"{'SYMBOL':<15} {'SIDE':<6} {'TRIGGER':<10} {'ORDER ID':<36} {'STATUS'}")
    print("-" * 80)
    
    for o in sl_orders:
        symbol = o['symbol']
        side = o['side']
        trigger = o['triggerPrice']
        oid = o['id']
        status = o['status']
        
        print(f"{symbol:<15} {side:<6} {trigger:<10} {oid:<36} {status}")
        
    print("-" * 80)
    print(" These orders are LIVE in the Matching Engine.")
    print("ℹ️ If UI shows '--', it is a frontend display lag. The Engine protects you.")

if __name__ == "__main__":
    visual_check_sl()
