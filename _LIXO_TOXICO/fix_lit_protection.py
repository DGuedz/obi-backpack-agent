import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)

def fix_lit_protection():
    print(" EMERGENCY: FIXING LIT PROTECTION & CLEANING ORDER LIMITS")
    
    # 1. Get Open Orders & Positions
    orders = data.get_open_orders()
    positions = data.get_positions()
    
    # Map active symbols (non-zero qty)
    active_symbols = set()
    for p in positions:
        if float(p['quantity']) != 0:
            active_symbols.add(p['symbol'])
    
    print(f"    Active Positions: {list(active_symbols)}")
    
    # 2. Cancel Orphans (Orders for symbols with no position)
    cancelled_count = 0
    for o in orders:
        symbol = o['symbol']
        oid = o['id']
        otype = o['orderType']
        
        if symbol not in active_symbols:
            print(f"   ️ Canceling ORPHAN order {oid} ({otype}) for {symbol}...")
            trade.cancel_open_orders(symbol) # Cancels all for this symbol, simpler
            cancelled_count += 1
            time.sleep(0.2)
            
    if cancelled_count > 0:
        print(f"    Cleaned {cancelled_count} orphan order signals. Slots freed.")
        time.sleep(1) # Wait for propagation
    else:
        print("   ️ No orphan orders found. Limit might be real.")

    # 3. Apply SL for LIT
    SYMBOL = "LIT_USDC_PERP"
    SL_PRICE = 1.642
    
    # Check if we have the position
    pos = next((p for p in positions if p['symbol'] == SYMBOL), None)
    if not pos:
        print(f"    CRITICAL: Position for {SYMBOL} not found!")
        return

    qty = pos['quantity']
    print(f"   ️ Applying SL for {SYMBOL} (Qty: {qty}) @ {SL_PRICE}")
    
    # Execute SL
    res_sl = trade.execute_order(
        symbol=SYMBOL,
        side="Ask", # Long -> Sell to Stop
        order_type="Market",
        quantity=qty,
        price=None,
        trigger_price=str(SL_PRICE)
    )
    
    if res_sl and 'id' in res_sl:
        print(f"    SL PLACED SUCCESSFULLY: ID {res_sl['id']}")
    else:
        print(f"    FAILED TO PLACE SL: {res_sl}")

if __name__ == "__main__":
    fix_lit_protection()
