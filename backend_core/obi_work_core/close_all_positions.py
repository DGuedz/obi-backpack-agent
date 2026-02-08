import sys
import os
import time

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

def close_all():
    print("🧹 STARTING POSITION CLEANUP...")
    client = BackpackClient()
    positions = client.get_positions()
    
    if not positions:
        print("✅ No open positions found.")
        return

    print(f"Found {len(positions)} open positions.")
    
    for pos in positions:
        symbol = pos.get('symbol')
        side = pos.get('side') # "Long" or "Short"
        quantity = abs(float(pos.get('quantity', 0)))
        entry_price = float(pos.get('entryPrice', 0))
        
        if quantity == 0:
            continue
            
        print(f"-> Closing {side} {symbol} (Size: {quantity}, Entry: {entry_price})")
        
        if not side:
            print("   ⚠️ Unknown side. Skipping.")
            continue
        
        # Determine close side
        exec_side = "Ask" if side.lower() == "long" else "Bid"
        
        # Execute Market Close
        res = client.execute_order(
            symbol=symbol,
            side=exec_side,
            order_type="Market",
            quantity=quantity
        )
        
        if res and 'id' in res:
            print(f"   ✅ Close Order Sent: {res['id']}")
        else:
            print("   ❌ Failed to close position.")
            
        time.sleep(0.5)

    print("Cleanup Complete.")

if __name__ == "__main__":
    close_all()
