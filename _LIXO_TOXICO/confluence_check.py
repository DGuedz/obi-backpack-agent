
import os
import time
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
indicators = BackpackIndicators()

def check_triple_confluence():
    symbol = "IP_USDC_PERP"
    print(f" TRIPLE CONFLUENCE CHECK: {symbol}")
    print("========================================")
    
    # 1. Technical Setup (RSI + BB)
    klines = data.get_klines(symbol, interval="5m", limit=50)
    df = pd.DataFrame(klines)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    rsi = indicators.calculate_rsi(df).iloc[-1]
    bb = indicators.calculate_bollinger_bands(df)
    price = df['close'].iloc[-1]
    upper = bb['upper'].iloc[-1]
    lower = bb['lower'].iloc[-1]
    
    tech_score = 0
    tech_bias = "NEUTRAL"
    
    if rsi < 35 and price <= lower:
        tech_score = 1
        tech_bias = "BULLISH (Oversold)"
    elif rsi > 65 and price >= upper:
        tech_score = 1
        tech_bias = "BEARISH (Overbought)"
        
    print(f"   1. Technical: {tech_bias} | RSI: {rsi:.1f} | BB: {lower:.4f}-{upper:.4f}")
    
    # 2. Flow Confirmation (Order Book Imbalance)
    depth = data.get_depth(symbol)
    bids = depth.get('bids', [])[:10]
    asks = depth.get('asks', [])[:10]
    
    bid_vol = sum([float(x[1]) for x in bids])
    ask_vol = sum([float(x[1]) for x in asks])
    
    imbalance = bid_vol / ask_vol if ask_vol > 0 else 1
    
    flow_score = 0
    flow_bias = "NEUTRAL"
    
    if imbalance > 2.0:
        flow_score = 1
        flow_bias = "BULLISH (Buy Wall)"
    elif imbalance < 0.5: # 1/2.0
        flow_score = 1
        flow_bias = "BEARISH (Sell Wall)"
        
    print(f"   2. Flow: {flow_bias} | Imbalance: {imbalance:.2f}x (Bids/Asks)")
    
    # 3. Price Trigger (Momentum)
    # Check last 3 candles for clear direction
    last_3 = df.iloc[-3:]
    closes = last_3['close'].values
    opens = last_3['open'].values
    
    momentum_score = 0
    momentum_bias = "CHOPPY"
    
    if all(c > o for c, o in zip(closes, opens)):
        momentum_score = 1
        momentum_bias = "BULLISH (3 Green Soldiers)"
    elif all(c < o for c, o in zip(closes, opens)):
        momentum_score = 1
        momentum_bias = "BEARISH (3 Black Crows)"
        
    print(f"   3. Momentum: {momentum_bias}")
    
    # FINAL VERDICT
    print("\n    VERDICT:")
    if tech_bias.startswith("BULLISH") and flow_bias.startswith("BULLISH"):
        print("       GREEN LIGHT: LONG (Confluence Confirmed)")
        return "LONG"
    elif tech_bias.startswith("BEARISH") and flow_bias.startswith("BEARISH"):
        print("       GREEN LIGHT: SHORT (Confluence Confirmed)")
        return "SHORT"
    else:
        print("       RED LIGHT: No Confluence. Hold Fire.")
        return "WAIT"

if __name__ == "__main__":
    check_triple_confluence()
