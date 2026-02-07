import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

SYMBOL = "AVAX_USDC_PERP"
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.05

def fix_avax():
    print(f" EMERGENCY FIX: {SYMBOL}")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Confirm Position
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == SYMBOL and float(p['netQuantity']) != 0), None)
    
    if not pos:
        print(" AVAX Position not found. Might have been closed.")
        return

    qty = abs(float(pos['netQuantity']))
    entry = float(pos['entryPrice'])
    side = pos['side'] # Should be "Short" based on report
    
    print(f"   Position: {side} {qty} @ {entry}")
    
    # 2. Calculate Protection
    if side == "Short":
        # SL above entry
        sl_price = entry * (1 + STOP_LOSS_PCT)
        # TP below entry
        tp_price = entry * (1 - TAKE_PROFIT_PCT)
        exit_side = "Bid" # Buy to cover
    else:
        # SL below entry
        sl_price = entry * (1 - STOP_LOSS_PCT)
        # TP above entry
        tp_price = entry * (1 + TAKE_PROFIT_PCT)
        exit_side = "Ask" # Sell to close
        
    sl_price = round(sl_price, 2) # AVAX decimals
    tp_price = round(tp_price, 2)
    
    print(f"   ️ Placing SL @ {sl_price}")
    print(f"    Placing TP @ {tp_price}")
    
    # 3. Execute
    try:
        # SL (Trigger Market)
        res_sl = trade.execute_order(
            symbol=SYMBOL,
            side=exit_side,
            order_type="Market",
            quantity=str(qty),
            price=None,
            trigger_price=str(sl_price)
        )
        print(f"    SL Result: {res_sl.get('id') if res_sl else 'Failed'}")
        
        # TP (Limit)
        res_tp = trade.execute_order(
            symbol=SYMBOL,
            side=exit_side,
            order_type="Limit",
            quantity=str(qty),
            price=str(tp_price)
        )
        print(f"    TP Result: {res_tp.get('id') if res_tp else 'Failed'}")
        
    except Exception as e:
        print(f"    Error: {e}")

if __name__ == "__main__":
    fix_avax()
