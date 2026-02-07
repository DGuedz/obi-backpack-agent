import os
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"
NEW_EXIT_TARGET = 90800.0 # Front-running the 10 BTC Wall at $90,828

def adjust_exit_strategy():
    print("\n [REALITY CHECK] ADJUSTING EXIT TO WHALE WALL...")
    print(f"    New Target: ${NEW_EXIT_TARGET:,.2f}")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Cancel Existing Orders (The $92k dream)
    print("    Cancelling old orders...")
    try:
        trade.cancel_all_orders(SYMBOL)
    except Exception as e:
        print(f"   ️ Cancel Error: {e}")
        
    # 2. Check Position
    positions = data.get_positions()
    btc_pos = [p for p in positions if p['symbol'] == SYMBOL]
    
    if btc_pos:
        pos = btc_pos[0]
        qty = float(pos.get('quantity', 0))
        entry = float(pos.get('entryPrice', 0))
        
        print(f"   ️ Position: {qty} BTC @ ${entry:,.2f}")
        
        # 3. Place New Limit Order
        print(f"   ️ Placing LIMIT SELL @ ${NEW_EXIT_TARGET:,.2f}...")
        res = trade.execute_order(
            SYMBOL,
            "Ask",
            NEW_EXIT_TARGET,
            qty,
            order_type="Limit",
            reduce_only=True,
            time_in_force="GTC"
        )
        
        if res:
            print("    ORDER UPDATED. We are now front-running the resistance.")
            loss_est = (NEW_EXIT_TARGET - entry) * qty
            print(f"    Estimated Realized Loss: ${loss_est:.2f}")
            print("    Better to lose small than lose everything.")
    else:
        print("   ℹ️ No position found to exit.")

if __name__ == "__main__":
    adjust_exit_strategy()
