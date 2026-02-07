
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

def adjust_shields_ip():
    symbol = "IP_USDC_PERP"
    print(f"️ ADJUSTING SHIELDS FOR {symbol} (SL 2% / TP 5%)...")
    
    # 1. Get Position
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == symbol), None)
    
    if not pos:
        print(f" No active position found for {symbol}. Cannot adjust.")
        return

    qty = float(pos['quantity']) # Absolute value from API usually positive, check side
    entry_price = float(pos['entryPrice'])
    side = pos['side'] # "Short" or "Long"
    
    print(f"   Position: {side} {qty} @ {entry_price}")
    
    # 2. Cancel Old Shields
    print("   ️ Cancelling old protection orders...")
    trade.cancel_open_orders(symbol)
    
    # 3. Calculate New Levels
    # SL 2%, TP 5%
    if side == "Short":
        # Short: TP below, SL above
        tp_price = entry_price * (1 - 0.05) # -5%
        sl_price = entry_price * (1 + 0.02) # +2%
        exit_side = "Bid" # Buy to cover
    else:
        # Long: TP above, SL below
        tp_price = entry_price * (1 + 0.05) # +5%
        sl_price = entry_price * (1 - 0.02) # -2%
        exit_side = "Ask" # Sell to close
        
    print(f"    New TP: {tp_price:.4f} (+5%)")
    print(f"    New SL: {sl_price:.4f} (-2%)")
    
    # 4. Deploy New Shields
    # TP (Limit ReduceOnly)
    trade.execute_order(
        symbol=symbol,
        side=exit_side,
        price=f"{tp_price:.4f}",
        quantity=str(qty),
        order_type="Limit",
        reduce_only=True
    )
    
    # SL (Trigger Limit - using "TriggerLimit" or "StopLimit" based on API check)
    # The previous log said "StopLimit" failed parsing: `Expected input type "OrderTypeEnum", found "StopLimit"`
    # Valid types usually: Limit, Market. Triggers are separate params?
    # NO. Backpack API docs say: orderType="Limit" or "Market". 
    # Conditional orders use `triggerPrice`. 
    # So to make a Stop Loss, we send orderType="Limit" (or Market) WITH triggerPrice.
    
    # Let's try sending a LIMIT order with triggerPrice (Stop Limit)
    # Trigger = sl_price
    # Limit Price = slightly worse to ensure fill
    limit_sl = sl_price * 1.05 if side == "Short" else sl_price * 0.95
    
    # If API requires orderType="Limit" even for StopLimit:
    res = trade.execute_order(
        symbol=symbol,
        side=exit_side,
        price=f"{limit_sl:.4f}",
        quantity=str(qty),
        order_type="Limit", # Use Limit type
        trigger_price=f"{sl_price:.4f}", # Add trigger
        reduce_only=True
    )
    
    if res and 'id' in res:
        print("    New Shields Active.")
    else:
        print(f"   ️ Warning: SL placement might have failed. Response: {res}")

if __name__ == "__main__":
    adjust_shields_ip()
