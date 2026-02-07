import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

SYMBOL = "FOGO_USDC_PERP"
CORRECT_SL_PCT = 0.02

def fix_fogo_sl():
    print(f" FIXING SL for {SYMBOL}...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Get Position Entry
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == SYMBOL and float(p['netQuantity']) != 0), None)
    
    if not pos:
        print(" No Position found.")
        return

    entry_price = float(pos['entryPrice'])
    quantity = abs(float(pos['netQuantity']))
    side = pos['side']
    
    print(f"   Position: {side} @ {entry_price}")
    
    # 2. Cancel Bad SL
    orders = data.get_open_orders()
    for o in orders:
        if o['symbol'] == SYMBOL and o.get('triggerPrice'):
            trigger = float(o['triggerPrice'])
            # Check if it's the "bad" one (higher than entry for Long SL)
            # Or just cancel ALL stops to be safe and replace.
            print(f"   ️ Cancelling existing Trigger Order @ {trigger}")
            trade.cancel_open_orders(SYMBOL) # Use cancel_all for simplicity or get specific ID
            # cancel_open_orders cancels ALL. I might lose the TP.
            # Better to cancel specifically?
            # API cancel_order(symbol, orderId)
            # But backpack_trade.py only has cancel_open_orders(symbol) (Cancel All) or cancel_all_orders.
            # Wait, backpack_trade.py has `cancel_open_orders(symbol=None)`.
            # Let's check `backpack_trade.py`.
            # It has `cancel_all_orders(symbol)`.
            # I will cancel ALL for FOGO and recreate both TP and SL. Safer.
            
    trade.cancel_all_orders(SYMBOL)
    print("    All FOGO orders cancelled. Rebuilding...")
    
    # 3. Place Correct SL
    sl_price = entry_price * (1 - CORRECT_SL_PCT) if side == "Long" else entry_price * (1 + CORRECT_SL_PCT)
    sl_price = round(sl_price, 6)
    
    print(f"   ️ Placing NEW SL @ {sl_price} (-2%)")
    try:
        trade.execute_order(
            symbol=SYMBOL,
            side="Ask" if side == "Long" else "Bid",
            order_type="Market",
            quantity=str(quantity),
            price=None,
            trigger_price=str(sl_price)
        )
        print("    SL Placed.")
    except Exception as e:
        print(f"    SL Failed: {e}")

    # 4. Replace TP
    tp_price = entry_price * (1 + 0.04) if side == "Long" else entry_price * (1 - 0.04)
    tp_price = round(tp_price, 6)
    
    print(f"    Placing NEW TP @ {tp_price} (+4%)")
    try:
        trade.execute_order(
            symbol=SYMBOL,
            side="Ask" if side == "Long" else "Bid",
            order_type="Limit",
            quantity=str(quantity),
            price=str(tp_price)
        )
        print("    TP Placed.")
    except Exception as e:
        print(f"    TP Failed: {e}")

if __name__ == "__main__":
    fix_fogo_sl()
