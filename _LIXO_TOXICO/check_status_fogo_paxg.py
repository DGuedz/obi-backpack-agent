import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()

def check_status():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()

    print("---  STATUS CHECK ---")
    
    # 1. FOGO Status
    print("\n[FOGO_USDC_PERP]")
    orders = data.get_open_orders()
    fogo_orders = [o for o in orders if o['symbol'] == 'FOGO_USDC_PERP']
    
    positions = data.get_positions()
    fogo_pos = next((p for p in positions if p['symbol'] == 'FOGO_USDC_PERP' and float(p['netQuantity']) != 0), None)
    
    if fogo_pos:
        print(f" POSITION OPEN: {fogo_pos['side']} {fogo_pos['netQuantity']} @ {fogo_pos['entryPrice']}")
    
    if fogo_orders:
        print(f"⏳ ORDERS OPEN: {len(fogo_orders)}")
        for o in fogo_orders:
            print(f"   - {o['side']} {o['orderType']} Price:{o.get('price')} Trigger:{o.get('triggerPrice')} ({o['status']})")
    elif not fogo_pos:
        print(" No Position or Open Orders.")

    # 2. PAXG Analysis
    print("\n[PAXG_USDC_PERP Analysis]")
    symbol = "PAXG_USDC_PERP"
    try:
        klines = data.get_klines(symbol, interval="15m", limit=50)
        if klines:
            df = pd.DataFrame(klines)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            rsi = indicators.calculate_rsi(df).iloc[-1]
            bb = indicators.calculate_bollinger_bands(df)
            price = df['close'].iloc[-1]
            upper = bb['upper'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            sma = bb['middle'].iloc[-1]
            
            trend = "BULL" if price > sma else "BEAR"
            
            print(f"   Price: {price}")
            print(f"   RSI: {rsi:.2f}")
            print(f"   Trend: {trend}")
            
            # Setup Check
            if trend == "BULL" and rsi < 40:
                print("    OPPORTUNITY: Pullback in Uptrend (Buy Dip)")
            elif trend == "BULL" and price > upper:
                print("   ️ OVERBOUGHT: Riding Upper Band (Momentum)")
            else:
                print("    No clear immediate setup.")
        else:
            print("   ️ No Data.")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    check_status()
