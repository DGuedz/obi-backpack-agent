import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

def audit_compliance():
    print(" COMPLIANCE AUDIT INITIATED: CHECKING SL/TP")
    print("=============================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Get All Positions
    positions = data.get_positions()
    open_positions = [p for p in positions if float(p['netQuantity']) != 0]
    
    if not open_positions:
        print(" No Open Positions to Audit.")
    
    # 2. Get All Open Orders
    orders = data.get_open_orders()
    
    # 3. Match Positions with Protections
    for pos in open_positions:
        symbol = pos['symbol']
        side = pos['side'] # Long or Short
        qty = abs(float(pos['netQuantity']))
        entry = float(pos['entryPrice'])
        
        print(f"\n AUDITING {symbol} ({side} {qty})")
        
        # Find SL and TP
        has_sl = False
        has_tp = False
        
        pos_orders = [o for o in orders if o['symbol'] == symbol]
        
        for o in pos_orders:
            # TP Check (Limit Order on opposite side, usually ReduceOnly or just opposite)
            # SL Check (Trigger Order on opposite side)
            
            is_opposite = (side == "Long" and o['side'] == "Ask") or (side == "Short" and o['side'] == "Bid")
            
            if is_opposite:
                if o['orderType'] == "Limit" and not o.get('triggerPrice'):
                    has_tp = True
                    print(f"    TP DETECTED: Limit @ {o['price']}")
                elif o.get('triggerPrice'):
                    has_sl = True
                    print(f"    SL DETECTED: Trigger @ {o['triggerPrice']}")
        
        # 4. ENFORCE COMPLIANCE
        if not has_sl:
            print("    SL MISSING! VIOLATION DETECTED.")
            print("   ️ PLACING EMERGENCY STOP LOSS...")
            # SL Distance: 2%
            sl_price = entry * 0.98 if side == "Long" else entry * 1.02
            
            # Robust Rounding
            if sl_price >= 1000: sl_price = round(sl_price, 1)
            elif sl_price >= 10: sl_price = round(sl_price, 2)
            elif sl_price >= 1: sl_price = round(sl_price, 4)
            else: sl_price = round(sl_price, 6)
            
            try:
                trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    order_type="Market",
                    quantity=str(qty),
                    price=None,
                    trigger_price=str(sl_price)
                )
                print(f"   ️ SL ENFORCED @ {sl_price}")
            except Exception as e:
                print(f"    FAILED TO PLACE SL: {e}")
        
        if not has_tp:
            print("    TP MISSING! VIOLATION DETECTED.")
            print("   ️ PLACING EMERGENCY TAKE PROFIT...")
            # TP Distance: 5%
            tp_price = entry * 1.05 if side == "Long" else entry * 0.95
            
            # Robust Rounding
            if tp_price >= 1000: tp_price = round(tp_price, 1)
            elif tp_price >= 10: tp_price = round(tp_price, 2)
            elif tp_price >= 1: tp_price = round(tp_price, 4)
            else: tp_price = round(tp_price, 6)
            
            try:
                trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    order_type="Limit",
                    quantity=str(qty),
                    price=str(tp_price)
                )
                print(f"    TP ENFORCED @ {tp_price}")
            except Exception as e:
                print(f"    FAILED TO PLACE TP: {e}")

    print("\n AUDIT COMPLETE.")

if __name__ == "__main__":
    audit_compliance()
