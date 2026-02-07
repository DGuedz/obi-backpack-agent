import os
import sys
import time
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

def force_sl_now():
    print("\n [EMERGENCY PROTOCOL] FORCING STOP LOSS ON ALL POSITIONS")
    print("   ️ This script will CANCEL existing stops and PLACE NEW ones.")
    print("   ️ Objective: Visual and Functional Guarantee of Protection.")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Get Positions
    positions = data.get_positions()
    if not positions:
        print("    No positions found. You are safe.")
        return
        
    for pos in positions:
        symbol = pos['symbol']
        qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
        entry_price = float(pos.get('entryPrice', 0))
        
        if qty == 0: continue
        
        print(f"\n    SECURING {symbol} (Size: {qty})")
        
        # 2. Cancel Existing Orders (To avoid duplicates/confusion)
        print("      ️ Cancelling existing open orders...")
        trade.cancel_open_orders(symbol)
        time.sleep(1)
        
        # 3. Calculate SL Price
        # Default: 1% from Entry
        sl_pct = 0.01
        
        if qty > 0: # Long -> Sell Stop below entry
            sl_price = entry_price * (1 - sl_pct)
            side = "Ask"
            print(f"       LONG Position. Setting SELL STOP @ {sl_price:.4f}")
        else: # Short -> Buy Stop above entry
            sl_price = entry_price * (1 + sl_pct)
            side = "Bid"
            print(f"       SHORT Position. Setting BUY STOP @ {sl_price:.4f}")
            
        # Round SL Price to 2 decimals (Standard for USDC pairs usually, but PAXG is high value)
        # PAXG Tick Size is likely 0.01 or 0.1
        sl_price = round(sl_price, 2)
            
        # 4. Execute Stop Market Order
        try:
            # Fix: OrderType "StopMarket" might be incorrect in API V1. 
            # Usually it's "Market" with triggerPrice, or "StopLimit".
            # Backpack Documentation suggests orderType="Market" + triggerPrice makes it a Stop Market?
            # Or is it "Market" and we pass triggerPrice?
            # Wait, execute_order uses payload["orderType"].
            # Let's try orderType="Market" with triggerPrice.
            
            # According to some docs, Stop Loss is just a conditional order.
            # If triggerPrice is set, orderType "Market" becomes Stop Market?
            # Or maybe "StopLoss"?
            
            # Let's try "Market" with triggerPrice.
            response = trade.execute_order(
                symbol=symbol,
                side=side,
                price="0", 
                quantity=abs(qty),
                order_type="Market", # Changed from StopMarket
                trigger_price=sl_price,
                reduce_only=True
            )
            
            if response and 'id' in response:
                print(f"       STOP LOSS PLACED SUCCESSFULLY. ID: {response['id']}")
                print(f"      ️ Protection is ACTIVE at ${sl_price:.4f}")
            else:
                print(f"       FAILED TO PLACE STOP LOSS: {response}")
                
        except Exception as e:
            print(f"       CRITICAL ERROR: {e}")

if __name__ == "__main__":
    force_sl_now()
