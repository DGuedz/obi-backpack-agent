import os
import time
from dotenv import load_dotenv
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# Load environment variables
load_dotenv()

# Initialize BackpackTrade
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
trade = BackpackTrade(auth)
data = BackpackData(auth)

def fix_zec():
    SYMBOL = "ZEC_USDC_PERP"
    print(f" EMERGENCY FIX: {SYMBOL}")
    
    # 1. Get Current Position
    positions = data.get_positions()
    position = next((p for p in positions if p['symbol'] == SYMBOL), None)
    
    if not position:
        print(f"    No open position for {SYMBOL}. Nothing to fix.")
        return

    side = position['side']
    qty = position['quantity']
    entry_price = float(position['entryPrice'])
    mark_price = float(position['markPrice'])
    
    print(f"    Position Found: {side} {qty} @ {entry_price} (Mark: {mark_price})")

    # 2. Cancel Existing Orders for this symbol to avoid duplicates
    print("   ️ Canceling existing open orders...")
    trade.cancel_open_orders(SYMBOL)
    time.sleep(1)

    # 3. Calculate Protection Levels
    # ZEC is Long. 
    # Current Price ~369.90. Entry 368.50.
    # We are in profit. Let's protect Breakeven + fees if possible, or tight SL.
    
    # SL: Just below entry to allow breathing room or Break Even if well in profit.
    # Let's put SL at 365.0 (approx 1% risk) - wait, user wants profit.
    # Entry 368.5. 1.5% SL = 368.5 * 0.985 = 362.9
    # Let's use a standard 2% safety SL for now to be safe.
    sl_price = round(entry_price * 0.98, 2) # 2% SL
    
    # TP: 5% Target
    tp_price = round(entry_price * 1.05, 2)

    print(f"   ️ Applying Protection: SL {sl_price} | TP {tp_price}")

    # 4. Execute Orders
    # Convert Side to Bid/Ask
    # If we are Long, we need to Sell (Ask) to close/stop.
    # If we are Short, we need to Buy (Bid) to close/stop.
    if side == "Long":
        exit_side = "Ask"
    else:
        exit_side = "Bid"

    try:
        # SL (Trigger Market)
        res_sl = trade.execute_order(
            symbol=SYMBOL,
            side=exit_side,
            order_type="Market",
            quantity=qty,
            price=None,
            trigger_price=str(sl_price)
        )
        print(f"    SL Set: {res_sl}")

        # TP (Limit)
        res_tp = trade.execute_order(
            symbol=SYMBOL,
            side=exit_side,
            order_type="Limit",
            quantity=qty,
            price=str(tp_price)
        )
        print(f"    TP Set: {res_tp}")

    except Exception as e:
        print(f"    Error executing protection orders: {e}")

if __name__ == "__main__":
    fix_zec()
