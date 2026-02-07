
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)
indicators = BackpackIndicators()

def project_blood_entry():
    symbol = "IP_USDC_PERP"
    print(f" PROJECTING BLOOD TRAIL ENTRY: {symbol}")
    
    # 1. Get Technical Structure (15m Context)
    klines = data.get_klines(symbol, interval="15m", limit=10)
    if not klines:
        print(" No data.")
        return

    df = pd.DataFrame(klines)
    cols = ['open', 'high', 'low', 'close', 'volume']
    for col in cols:
        df[col] = df[col].astype(float)
        
    # Find the recent "Dump Candle" (Biggest red candle)
    df['body'] = df['close'] - df['open']
    dump_candle = df.sort_values(by='body').iloc[0] # Most negative body
    
    high_w = dump_candle['high']
    low_w = dump_candle['low']
    current_price = df['close'].iloc[-1]
    
    print(f"    Dump Range: {high_w:.4f} (Top) -> {low_w:.4f} (Bottom)")
    print(f"    Current Price: {current_price:.4f}")
    
    # 2. Calculate Fibonacci Retracement (Dead Cat Bounce Levels)
    # We want to Short at 0.5 or 0.618 retracement of the dump
    range_dump = high_w - low_w
    fib_382 = low_w + (range_dump * 0.382)
    fib_500 = low_w + (range_dump * 0.500)
    fib_618 = low_w + (range_dump * 0.618)
    
    print(f"    Fib Levels (Short Zones):")
    print(f"      0.382: {fib_382:.4f}")
    print(f"      0.500: {fib_500:.4f} (Golden Zone)")
    print(f"      0.618: {fib_618:.4f} (Premium)")
    
    # 3. Check Order Book for Confirmation (Liquidity Walls)
    depth = data.get_depth(symbol)
    asks = depth.get('asks', [])
    
    # Find closest Ask Wall near Fib levels
    best_entry = fib_500 # Default
    wall_vol = 0
    
    for p, v in asks:
        price = float(p)
        vol = float(v)
        if fib_382 <= price <= fib_618:
            if vol > wall_vol:
                wall_vol = vol
                best_entry = price
                
    print(f"    Detected Sell Wall: {best_entry:.4f} (Vol: {wall_vol:.1f})")
    
    # 4. Project Entry
    # If current price is below Best Entry, place Limit Sell there.
    # If current price is above (unlikely if dumping), sell market? No, limit.
    
    print("\n️ EXECUTION PLAN (Blood Trail):")
    qty = 380 # Approx $1000 notional at 2.6
    
    if current_price < best_entry:
        print(f"    Strategy: LIMIT SELL (Short) at Retest")
        print(f"    Price: {best_entry:.4f}")
        print(f"    Qty: {qty}")
        
        # Execute Limit Order
        print("    PLACING TRAP ORDER...")
        trade.execute_order(
            symbol=symbol,
            side="Ask",
            price=f"{best_entry:.4f}",
            quantity=str(qty),
            order_type="Limit",
            post_only=True
        )
        
        # Protective Stop
        sl_price = high_w * 1.01 # Just above dump candle high
        print(f"   ️ SL Projection: {sl_price:.4f}")
        
    else:
        print("   ️ Price is already above Fib levels. Wait for exhaustion or Short Market if breaking low.")

if __name__ == "__main__":
    project_blood_entry()
