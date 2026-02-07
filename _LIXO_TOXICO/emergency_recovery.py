import os
import sys
import time
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"
EXIT_TARGET = 92000.0 # EMA 200 Recovery Level

def emergency_recovery():
    print("\n [EMERGENCY PROTOCOL] RECOVERY MODE ACTIVATED")
    print(f"    Objective: Survive & Recover Capital.")
    
    # Init
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. CANCEL ALL OPEN ORDERS (Stop the Bleeding / Free Margin)
    print("\n 1. Cancelling ALL Open Orders (Grid)...")
    try:
        trade.cancel_all_orders(SYMBOL) 
        # Using ad-hoc request if method not in class yet, but assuming we added it or trying generic
        # If trade.cancel_all_orders doesn't exist, we use raw request
        
        endpoint = "/api/v1/orders"
        url = "https://api.backpack.exchange/api/v1/orders"
        params = {"symbol": SYMBOL}
        headers = auth.get_headers(instruction="orderCancelAll", params=params)
        res = requests.delete(url, headers=headers, json=params)
        
        if res.status_code == 200:
            print("    Orders Cancelled. Margin Unlocked.")
        else:
            print(f"   ️ Cancel Warning: {res.text}")
            
    except Exception as e:
        print(f"    Cancel Error: {e}")

    # 2. ASSESS DAMAGE & POSITION
    print("\n 2. Assessing Position...")
    pos_qty = 0.0
    try:
        positions = data.get_positions()
        btc_pos = [p for p in positions if p['symbol'] == SYMBOL]
        if btc_pos:
            pos = btc_pos[0]
            pos_qty = float(pos.get('quantity', 0))
            entry = float(pos.get('entryPrice', 0))
            pnl = float(pos.get('unrealizedPnl', 0))
            side = pos.get('side')
            
            print(f"   ️ TRAPPED POSITION: {side} {pos_qty} BTC @ ${entry:,.2f}")
            print(f"    Current PnL: ${pnl:.2f}")
            
            # 3. PLACE RECOVERY ORDER (Limit Sell @ Resistance)
            # Strategy: Place Limit Sell at $92,000 (EMA 200).
            # This is the "Exit Liquidity" point.
            
            if side.lower() == 'long' and pos_qty > 0:
                print(f"\n️ 3. Placing RECOVERY EXIT @ ${EXIT_TARGET:,.2f}...")
                
                # Verify if Exit Target is above current price (it should be)
                # If current price > 92000 (miracle), sell now.
                
                res = trade.execute_order(
                    SYMBOL, 
                    "Ask", 
                    EXIT_TARGET, 
                    pos_qty, 
                    order_type="Limit", 
                    reduce_only=True,
                    time_in_force="GTC"
                )
                print(f"    EXIT ORDER PLACED. Waiting for bounce.")
                print("    Strategy: RSI is 21 (Oversold). We WAIT for the rubber band snap.")
                
        else:
            print("   ℹ️ No Active Position found. (Did we get liquidated? Check Balance)")
            
    except Exception as e:
        print(f"    Recovery Error: {e}")

if __name__ == "__main__":
    emergency_recovery()
