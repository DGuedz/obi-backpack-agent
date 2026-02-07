import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

def fix_night_guard():
    auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
    trade = BackpackTrade(auth)
    
    print(f" NIGHT GUARD FIX PROTOCOL...")
    
    # 1. FIX AAVE (Precision Error)
    # Entry ~146. Brackets need rounding to 2 decimals.
    symbol_aave = "AAVE_USDC_PERP"
    qty_aave = 0.08
    entry_aave = 146.425 # Approx from logs
    
    sl_aave = round(entry_aave * 1.03, 2) # Short SL (+3%)
    tp_aave = round(entry_aave * 0.93, 2) # Short TP (-7%)
    
    print(f" Fixing AAVE: SL {sl_aave} | TP {tp_aave}")
    try:
        trade.execute_order(symbol_aave, "Bid", "0", qty_aave, "StopLoss", trigger_price=str(sl_aave))
        trade.execute_order(symbol_aave, "Bid", "0", qty_aave, "TakeProfit", trigger_price=str(tp_aave))
        print(" AAVE Protected.")
    except Exception as e:
        print(f" AAVE Fix Failed: {e}")

    # 2. FIX PUMP (Order Limit Error)
    # Strategy: Use Guardian Angel (Software Stop) instead of Hard Order if limit reached.
    # BUT, we should try to cancel some old far-away orders if possible to free up slots.
    # checking open orders...
    print(" Fixing PUMP (Order Limit)...")
    try:
        orders = trade.get_open_orders()
        # Cancel oldest orders if > 10? No, risky.
        # Just try to place SL only first (Critical).
        symbol_pump = "PUMP_USDC_PERP"
        qty_pump = 4200
        entry_pump = 0.0028
        
        sl_pump = round(entry_pump * 1.03, 6)
        
        print(f"   Trying to force PUMP SL at {sl_pump}...")
        trade.execute_order(symbol_pump, "Bid", "0", qty_pump, "StopLoss", trigger_price=str(sl_pump))
        print(" PUMP SL Placed (hopefully).")
        
    except Exception as e:
        print(f" PUMP Fix Failed: {e}")
        print("   ️ GUARDIAN ANGEL MUST WATCH PUMP CLOSELY.")

if __name__ == "__main__":
    fix_night_guard()
