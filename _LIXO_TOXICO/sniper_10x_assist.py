import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# --- CONFIG ---
MARGIN_PER_SHOT = 100
LEVERAGE = 10
SL_PCT = 0.015  # 1.5% Stop Loss (Safety)
TP_PCT = 0.03   # 3% Take Profit (Target)
LOG_FILE = "sniper_shots_log.json"

# Load Env
load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
trade = BackpackTrade(auth)
data = BackpackData(auth)

def load_shots_log():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_shot_log(shot_data):
    logs = load_shots_log()
    logs.append(shot_data)
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=4)

def execute_sniper_shot(symbol, side):
    print(f"\n PREPARING SNIPER SHOT: {side} {symbol}")
    print(f"   Margin: ${MARGIN_PER_SHOT} | Leverage: {LEVERAGE}x")

    # 1. Get Market Info for Step Size / Tick Size
    markets = data.get_markets()
    market = next((m for m in markets if m['symbol'] == symbol), None)
    if not market:
        print(f" Market {symbol} not found.")
        return

    # 2. Get Current Price
    ticker = data.get_ticker(symbol)
    if not ticker:
        print(" Failed to get ticker.")
        return
    
    current_price = float(ticker['lastPrice'])
    print(f"   Current Price: {current_price}")

    # 3. Calculate Quantity
    # Notional = Margin * Leverage
    # Qty = Notional / Price
    notional = MARGIN_PER_SHOT * LEVERAGE
    raw_qty = notional / current_price
    
    # Adjust for Step Size (avoid decimal errors)
    step_size = float(market['filters']['quantity']['stepSize'])
    
    # Simple rounding to step size
    if step_size >= 1.0:
        qty = int(raw_qty)
    else:
        # Round to appropriate decimals
        decimals = 0
        temp = step_size
        while temp < 1:
            temp *= 10
            decimals += 1
        qty = round(raw_qty, decimals)

    print(f"   Calculated Qty: {qty} (Notional: ${notional})")

    if qty <= 0:
        print(" Quantity is zero. Price too high or margin too low.")
        return

    # 4. Confirm Margin Available?
    # We assume user knows, but let's check?
    # Skip for speed, trust the plan.

    # 5. EXECUTE ENTRY (Market)
    print("    FIRING ENTRY...")
    # Convert side: "Long" -> "Bid", "Short" -> "Ask"
    # Wait, trade.execute_order expects "Bid" or "Ask"
    order_side = "Bid" if side.lower() == "long" else "Ask"
    
    res_entry = trade.execute_order(
        symbol=symbol,
        side=order_side,
        order_type="Market",
        quantity=qty,
        price=None
    )
    
    if not res_entry or 'id' not in res_entry:
        print(f" Entry Failed: {res_entry}")
        return

    entry_id = res_entry['id']
    print(f"    ENTRY CONFIRMED! ID: {entry_id}")
    
    # 6. GUARDIAN PROTOCOL (Immediate SL/TP)
    print("   ️ ACTIVATING GUARDIAN PROTOCOL...")
    
    # Calculate Prices
    if side.lower() == "long":
        sl_price = current_price * (1 - SL_PCT)
        tp_price = current_price * (1 + TP_PCT)
        exit_side = "Ask"
    else:
        sl_price = current_price * (1 + SL_PCT)
        tp_price = current_price * (1 - TP_PCT)
        exit_side = "Bid"

    # Round Prices to Tick Size
    tick_size = float(market['filters']['price']['tickSize'])
    # Logic to round price to tick size
    # Simplification: use round based on tick size decimals
    tick_decimals = 0
    temp_tick = tick_size
    while temp_tick < 1:
        temp_tick *= 10
        tick_decimals += 1
    
    sl_price = round(sl_price, tick_decimals)
    tp_price = round(tp_price, tick_decimals)

    # Place SL (Trigger Market)
    res_sl = trade.execute_order(
        symbol=symbol,
        side=exit_side,
        order_type="Market",
        quantity=qty,
        price=None,
        trigger_price=str(sl_price)
    )
    
    # Place TP (Limit)
    res_tp = trade.execute_order(
        symbol=symbol,
        side=exit_side,
        order_type="Limit",
        quantity=qty,
        price=str(tp_price)
    )

    print(f"    SL Set @ {sl_price}: {'' if res_sl and 'id' in res_sl else ''}")
    print(f"    TP Set @ {tp_price}: {'' if res_tp and 'id' in res_tp else ''}")

    # Log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "shot_number": len(load_shots_log()) + 1,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "entry_price": current_price,
        "sl": sl_price,
        "tp": tp_price,
        "status": "OPEN"
    }
    save_shot_log(log_entry)
    print(f"    Logged Shot #{log_entry['shot_number']}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 sniper_10x_assist.py <SYMBOL> <SIDE>")
        print("Example: python3 sniper_10x_assist.py SOL_USDC_PERP Long")
    else:
        s_symbol = sys.argv[1]
        s_side = sys.argv[2]
        execute_sniper_shot(s_symbol, s_side)
