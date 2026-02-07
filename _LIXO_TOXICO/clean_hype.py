
import os
import time
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)

def clean_hype():
    symbol = "HYPE_USDC_PERP"
    print(f" STARTING CLEANUP FOR {symbol}...")
    
    # 1. Get Position
    positions = data.get_positions()
    target_pos = next((p for p in positions if p['symbol'] == symbol), None)
    
    if not target_pos:
        print(f" No active position found for {symbol}. It is clean.")
        return
        
    qty = float(target_pos['quantity'])
    side = target_pos['side']
    print(f"️ FOUND POSITION: {side} {qty} {symbol}")
    
    # 2. Force Close (Market)
    print(" EXECUTING FORCE CLOSE (MARKET)...")
    res = trade.close_position(symbol, qty if side == 'Long' else -qty)
    
    if res:
        print(f" FORCE CLOSE SENT: {res.get('id', 'Unknown ID')}")
    else:
        print(" FAILED TO SEND CLOSE ORDER.")
        
    # 3. Cancel Open Orders
    print("️ CANCELLING OPEN ORDERS...")
    trade.cancel_open_orders(symbol)
    
    # 4. Verify
    time.sleep(2)
    positions = data.get_positions()
    target_pos = next((p for p in positions if p['symbol'] == symbol), None)
    if not target_pos:
        print(f" CLEANUP SUCCESSFUL: {symbol} is gone.")
    else:
        print(f"️ WARNING: {symbol} might still be open. Check manually.")

if __name__ == "__main__":
    clean_hype()
