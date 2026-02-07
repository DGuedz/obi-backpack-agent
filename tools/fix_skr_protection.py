import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

def fix_skr():
    auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
    trade = BackpackTrade(auth)
    
    symbol = "SKR_USDC_PERP"
    qty = 1190.0 # From previous log
    
    # Entry approx from log or market price?
    # Log said: " SENDING: Bid 1190.0 SKR_USDC_PERP"
    # Assuming filled around current price.
    # Market Scanner said 0.0167.
    entry_price = 0.0167 
    
    # Long Brackets: SL below, TP above
    # SL 1.5%, TP 4%
    sl_price = entry_price * (1 - 0.015)
    tp_price = entry_price * (1 + 0.04)
    
    # Formatting for low cap (4 decimals?)
    sl_price = round(sl_price, 4)
    tp_price = round(tp_price, 4)
    
    print(f" FIXING SKR PROTECTION...")
    print(f"   SL: {sl_price} | TP: {tp_price}")
    
    try:
        # Stop Loss (Sell Trigger -> Ask)
        print(f"️ Placing SL (Ask) at {sl_price}...")
        trade.execute_order(
            symbol=symbol,
            side="Ask", # Long Exit = Ask
            price="0",
            quantity=qty,
            order_type="StopLoss",
            trigger_price=str(sl_price)
        )
        
        # Take Profit (Sell Trigger -> Ask)
        print(f" Placing TP (Ask) at {tp_price}...")
        trade.execute_order(
            symbol=symbol,
            side="Ask", # Long Exit = Ask
            price="0",
            quantity=qty,
            order_type="TakeProfit",
            trigger_price=str(tp_price)
        )
        print(" SKR Protected.")
        
    except Exception as e:
        print(f" SKR Fix Failed: {e}")

if __name__ == "__main__":
    fix_skr()
