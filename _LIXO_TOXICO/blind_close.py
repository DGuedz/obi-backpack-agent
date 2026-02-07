
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

def emergency_blind_close():
    symbol = "IP_USDC_PERP"
    print(f" EMERGENCY BLIND CLOSE: {symbol}")
    print("   Reason: User reports position active, API shows none (Ghost Position).")
    
    # Strategy: Fire Market Orders in both directions? No, that opens hedge.
    # We must know direction. User said "Short" entry manual.
    # So we need to BUY to close.
    
    # Force Buy 388 IP (Approx qty from previous manual entry)
    qty = 388 # Hardcoded from manual entry log (388.5 was estimate, let's try chunks)
    
    print(f"    Firing Blind BUY Order (Qty: {qty})...")
    
    res = trade.execute_order(
        symbol=symbol,
        side="Bid", # Buy to Close Short
        price=None,
        quantity=str(qty),
        order_type="Market",
        reduce_only=True # Critical! Only close if exists.
    )
    
    if res and 'id' in res:
        print(f"    BLIND CLOSE SENT: {res['id']}")
    else:
        print(f"    Blind Close Failed (Maybe no position to reduce?): {res}")
        
    # Double Tap (Small cleanup)
    time.sleep(1)
    print("    Firing Cleanup Round (Qty: 10)...")
    trade.execute_order(symbol, "Bid", None, "10", "Market", reduce_only=True)

if __name__ == "__main__":
    emergency_blind_close()
