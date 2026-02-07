import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

def free_slots():
    auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    print(" CLEANING UP ORPHAN ORDERS TO FREE SLOTS...")
    
    try:
        open_orders = data.get_open_orders()
        positions = data.get_positions()
        active_symbols = [p['symbol'] for p in positions if float(p['quantity']) != 0]
        
        print(f"   Active Positions: {active_symbols}")
        
        cancelled_count = 0
        for order in open_orders:
            symbol = order['symbol']
            
            # 1. Cancel Orphans (Orders for symbols we don't hold)
            if symbol not in active_symbols:
                print(f"   ️ Cancelling ORPHAN {symbol} order {order['id']}...")
                trade.cancel_open_order(symbol, order['id'])
                cancelled_count += 1
                
            # 2. Cancel Duplicate Protections (If > 2 orders per symbol, maybe cleanup?)
            # Too risky to automate blindly right now. Stick to orphans.
            
        print(f"    Cancelled {cancelled_count} orders.")
        
        pass
                
    except Exception as e:
        print(f" Error freeing slots: {e}")

if __name__ == "__main__":
    free_slots()
