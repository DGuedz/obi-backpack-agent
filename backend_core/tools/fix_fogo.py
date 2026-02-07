import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

def fix_fogo():
    auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
    trade = BackpackTrade(auth)
    
    symbol = "FOGO_USDC_PERP"
    qty = 560
    wrong_order_id = "29176990200"
    
    print(f" FIXING FOGO PROTECTION...")
    
    # 1. Cancel wrong order
    try:
        trade.cancel_open_order(symbol, wrong_order_id)
        print(" Cancelled wrong Bid Trigger.")
    except Exception as e:
        print(f"️ Failed to cancel (maybe already gone): {e}")

    # 2. Place Correct Stop Loss (SELL / ASK)
    sl_price = 0.033909
    print(f"️ Placing Correct SL (Sell) at {sl_price}...")
    trade.execute_order(
        symbol=symbol,
        side="Ask",
        price="0",
        quantity=qty,
        order_type="StopLoss", # Mapped to TriggerMarket internally
        trigger_price=str(sl_price)
    )
    
    # 3. Place Take Profit (SELL / ASK)
    tp_price = 0.0375 # Target ~4-5%
    print(f" Placing TP (Sell) at {tp_price}...")
    trade.execute_order(
        symbol=symbol,
        side="Ask",
        price="0",
        quantity=qty,
        order_type="TakeProfit", # Mapped to TriggerMarket internally
        trigger_price=str(tp_price)
    )

if __name__ == "__main__":
    fix_fogo()
