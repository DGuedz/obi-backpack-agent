import os
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# --- SNIPER CONFIG ---
SYMBOL = "BTC_USDC" # Correct Spot/Perp Symbol
LEVERAGE = 10
MARGIN_CAPITAL = 200 # $200
NOTIONAL_TARGET = MARGIN_CAPITAL * LEVERAGE # $2000
SL_PCT = 0.02 # 2% Structural Stop
TP_PCT = 0.05 # 5% Target

def sniper_entry():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    print(f"\n SNIPER SHOT ACTIVATED: {SYMBOL} [LONG]")
    print(f"    Power: ${NOTIONAL_TARGET} (${MARGIN_CAPITAL} x {LEVERAGE}x)")
    print(f"   ️ Protocol: AEGIS (Maker Only + Confluences)")
    print("==================================================")
    
    # 1. Fetch Candles for Confluence Check
    print("    Checking Market Structure (1h)...")
    # Correct method name is likely get_klines based on error
    try:
        candles = data.get_klines(SYMBOL, "1h", limit=100)
    except AttributeError:
        # Fallback to check if method exists or print available
        print("   ️ Method mismatch. Checking available methods...")
        candles = []
        
    if not candles:
        print("    Error: No candle data found or method error.")
        return

    df = pd.DataFrame(candles)
    df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
    df['close'] = df['close'].astype(float)
    
    # 2. Indicators Calculation
    rsi = indicators.calculate_rsi(df).iloc[-1]
    bb = indicators.calculate_bollinger_bands(df)
    lower_band = bb['lower'].iloc[-1]
    upper_band = bb['upper'].iloc[-1]
    current_price = df['close'].iloc[-1]
    ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
    
    print(f"    Technicals: Price=${current_price:.2f} | RSI={rsi:.2f} | EMA50=${ema_50:.2f}")
    
    # 3. AEGIS Validation Logic
    is_valid = True
    reasons = []
    
    # Trend Filter: Only Long if Price > EMA 50 (or recovering)
    if current_price < ema_50:
        # If below EMA, check if RSI is oversold (Counter-trend opportunity)
        if rsi < 35:
            reasons.append("️ Counter-Trend (Below EMA) but RSI Oversold (Sniper Entry)")
        else:
            is_valid = False
            reasons.append(" Bearish Trend (Price < EMA 50) & RSI Neutral")
    else:
        reasons.append(" Bullish Trend (Price > EMA 50)")
        
    # RSI Filter
    if rsi > 70:
        is_valid = False
        reasons.append(" RSI Overbought (>70) - Risk of Pullback")
    elif rsi < 30:
        reasons.append(" RSI Oversold (Sniper Value)")
    else:
        reasons.append(" RSI Neutral/Healthy")
        
    # Bollinger Filter (Value Area)
    # Ideally buy near lower band or mid band
    if current_price > upper_band:
        reasons.append("️ Price near Upper Band (Expensive)")
    
    # 4. Decision
    print("\n    DECISION MATRIX:")
    for r in reasons:
        print(f"   {r}")
        
    if not is_valid:
        print(f"\n    SNIPER ABORTED: Confluences not met.")
        return
        
    print("\n    SETUP VALIDATED. EXECUTING ORDER...")
    
    # 5. Execution (Maker Only)
    ticker = data.get_ticker(SYMBOL)
    best_bid = float(ticker.get('lastPrice', current_price)) # Use last price or slightly below for maker? 
    # To be Maker, we should place at Best Bid. 
    # But API ticker might not give bid/ask, checking depth briefly
    depth = data.get_depth(SYMBOL)
    if depth and depth.get('bids'):
        best_bid = float(depth['bids'][0][0])
    
    # Adjust price to be slightly competitive or just match best bid
    entry_price = best_bid 
    
    # Calculate Quantity
    # Notional = Price * Qty => Qty = Notional / Price
    qty = NOTIONAL_TARGET / entry_price
    
    # Rounding (Tick Size/Step Size) - Manual handling or use precision logic if available
    # Assuming BTC step size is usually 0.0001 or similar. Let's round to 4 decimals to be safe.
    qty = round(qty, 4)
    entry_price = round(entry_price, 1) # USDC typically 0.1 or 0.01
    
    print(f"    Placing MAKER Limit Order: {qty} BTC @ ${entry_price}")
    
    res = trade.execute_order(
        symbol=SYMBOL,
        side="Bid",
        price=entry_price,
        quantity=qty,
        order_type="Limit",
        post_only=True
    )
    
    if res and 'id' in res:
        print(f"    ORDER PLACED SUCCESSFULLY! ID: {res['id']}")
        
        # Calculate TP/SL Prices
        tp_price = entry_price * (1 + TP_PCT)
        sl_price = entry_price * (1 - SL_PCT)
        
        print(f"    TARGETS SET: TP=${tp_price:.2f} (+5%) | SL=${sl_price:.2f} (-2%)")
        print("   (Note: TP/SL orders should be managed by the Farm Bot or OCO if available)")
    else:
        print(f"    Order Failed: {res}")

if __name__ == "__main__":
    sniper_entry()
