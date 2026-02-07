
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

def panic_exit_ip():
    symbol = "IP_USDC_PERP"
    print(f" PANIC EXIT INITIATED FOR {symbol} ")
    
    # 1. Cancel Open Orders FIRST to prevent conflict or adding to position
    print("   ️ Cancelling all open orders...")
    trade.cancel_open_orders(symbol)
    
    # 2. Get Current Position
    print("    Checking position status...")
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == symbol), None)
    
    if not pos:
        print(f"    No active position found for {symbol}. You are safe.")
        return

    qty = float(pos['quantity'])
    side = pos['side']
    print(f"   ️ FOUND POSITION: {side} {qty} {symbol}")
    
    # 3. Market Close
    print(f"    EXECUTING MARKET CLOSE ({qty})...")
    # close_position expects signed quantity to determine direction (Negative = Short -> Buy to Close)
    # If API returns signed quantity, pass it directly.
    # The log showed "Short -694.3", so qty is negative.
    # close_position(-694.3) -> checks < 0 -> sets side="Bid" (Buy) -> Correct for Short.
    res = trade.close_position(symbol, qty)
    
    if res and 'id' in res:
        print(f"    EXIT ORDER SENT: {res['id']}")
    else:
        print(f"    EXIT FAILED. API RESPONSE: {res}")
        # Retry once?
        time.sleep(1)
        print("    Retrying Exit...")
        res = trade.close_position(symbol, qty if side == 'Long' else -qty)
        print(f"   Retry Result: {res}")

    # 4. Final Verification
    time.sleep(2)
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == symbol), None)
    if not pos:
        print(f"    CONFIRMED: {symbol} POSITION CLOSED.")
    else:
        print(f"    CRITICAL: Position might still be open: {pos['side']} {pos['quantity']}")

if __name__ == "__main__":
    panic_exit_ip()
