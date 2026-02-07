
import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)

def emergency_stop_all():
    print(" EMERGENCY STOP - PANIC BUTTON ACTIVATED ")
    print("================================================")
    
    # 1. Cancel ALL Open Orders (Shields/Limits)
    print("   ️ Cancelling ALL Open Orders (Global)...")
    trade.cancel_open_orders()
    
    # 2. Close ALL Active Positions (Market)
    positions = data.get_positions()
    print(f"    Found {len(positions)} active positions to NUKE.")
    
    for pos in positions:
        symbol = pos['symbol']
        side = pos['side']
        qty = float(pos['quantity'])
        
        print(f"    CLOSING {symbol} ({side} {qty})...")
        
        # Determine exit side
        # Long -> Sell (Ask)
        # Short -> Buy (Bid)
        # close_position usually handles direction if passed signed qty or we handle manually
        # Let's be explicit:
        exit_side = "Ask" if side == "Long" else "Bid"
        
        res = trade.execute_order(
            symbol=symbol,
            side=exit_side,
            price=None,
            quantity=str(qty),
            order_type="Market",
            reduce_only=True
        )
        
        if res and 'id' in res:
            print(f"       CLOSED: {res['id']}")
        else:
            print(f"       FAILED TO CLOSE {symbol}: {res}")
            
    print("\n    ALL SYSTEMS HALTED.")

if __name__ == "__main__":
    emergency_stop_all()
