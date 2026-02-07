import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

SYMBOL = "FOGO_USDC_PERP"
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04

def protect_fogo():
    print(f"️ GUARDIAN PROTOCOL: Checking {SYMBOL} Protection...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Check Position
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == SYMBOL and float(p['netQuantity']) != 0), None)
    
    if not pos:
        print(" No Position found to protect.")
        return

    quantity = abs(float(pos['netQuantity']))
    entry_price = float(pos['entryPrice'])
    side = pos['side'] # Long/Short
    
    print(f"    Position Found: {side} {quantity} @ {entry_price}")

    # 2. Check Existing Orders
    orders = data.get_open_orders()
    fogo_orders = [o for o in orders if o['symbol'] == SYMBOL]
    
    has_sl = False
    has_tp = False
    
    for o in fogo_orders:
        if o['side'] != side: # Opposite side (Sell if Long)
            if o['orderType'] == 'Limit' and not o.get('triggerPrice'):
                has_tp = True
                print(f"    TP Found: Limit @ {o['price']}")
            if o.get('triggerPrice'):
                has_sl = True
                print(f"    SL Found: Trigger @ {o['triggerPrice']}")

    # 3. Place Missing Orders
    if not has_sl:
        print("️ SL MISSING! Placing Stop Loss...")
        sl_price = entry_price * (1 - STOP_LOSS_PCT) if side == "Long" else entry_price * (1 + STOP_LOSS_PCT)
        sl_price = round(sl_price, 6)
        
        # Stop Market
        try:
            res = trade.execute_order(
                symbol=SYMBOL,
                side="Ask" if side == "Long" else "Bid",
                order_type="Market",
                quantity=str(quantity),
                price=None,
                trigger_price=str(sl_price)
            )
            print(f"   ️ SL Placed: {res.get('id')} @ {sl_price}")
        except Exception as e:
            print(f"    SL FAILED: {e}")

    if not has_tp:
        print("️ TP MISSING! Placing Take Profit...")
        tp_price = entry_price * (1 + TAKE_PROFIT_PCT) if side == "Long" else entry_price * (1 - TAKE_PROFIT_PCT)
        tp_price = round(tp_price, 6)
        
        try:
            res = trade.execute_order(
                symbol=SYMBOL,
                side="Ask" if side == "Long" else "Bid",
                order_type="Limit",
                quantity=str(quantity),
                price=str(tp_price)
            )
            print(f"    TP Placed: {res.get('id')} @ {tp_price}")
        except Exception as e:
            print(f"    TP FAILED: {e}")

if __name__ == "__main__":
    protect_fogo()
