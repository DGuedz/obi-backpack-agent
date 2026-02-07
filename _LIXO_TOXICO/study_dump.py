
import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def study_dump_mechanics():
    symbol = "IP_USDC_PERP"
    print(f" STUDYING DUMP MECHANICS: {symbol}")
    print("========================================")
    
    # 1. Fetch Granular Data (1m and 5m)
    klines_1m = data.get_klines(symbol, interval="1m", limit=60)
    klines_5m = data.get_klines(symbol, interval="5m", limit=24)
    
    if not klines_1m or not klines_5m:
        print(" Insufficient data.")
        return

    df = pd.DataFrame(klines_1m)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    # 2. Identify the Dump Event
    # Dump defined as largest negative candle or sequence
    df['change'] = (df['close'] - df['open']) / df['open']
    dump_idx = df['change'].idxmin()
    dump_candle = df.iloc[dump_idx]
    
    # Backpack API might return 'end' as string or not unit='s' compatible directly if already parsed?
    # Actually Backpack API klines usually have 'start' or 'end' as ISO strings or timestamps?
    # The error says "2026-01-19 00:03:00". It's already a string date.
    dump_time = dump_candle['end'] 
    
    dump_size = dump_candle['change'] * 100
    dump_vol = dump_candle['volume']
    
    print(f" The Dump Event:")
    print(f"   Size: {dump_size:.2f}% (Single Candle)")
    print(f"   Volume: {dump_vol:.0f} (Massive Liquidation)")
    
    # 3. Analyze Post-Dump Behavior (Recovery)
    # Price path since dump
    post_dump = df.iloc[dump_idx+1:]
    if post_dump.empty:
        print("   ️ Dump just happened. No recovery data yet.")
        return
        
    recovery_high = post_dump['high'].max()
    recovery_low = post_dump['low'].min()
    current_price = df['close'].iloc[-1]
    
    dump_top = dump_candle['high'] # Where it started falling
    dump_bottom = dump_candle['low'] # Where it stopped (initially)
    
    # Calculate Recovery Percentage (Retracement)
    total_drop = dump_top - recovery_low # Max drop from top of candle to lowest point after
    if total_drop == 0: total_drop = 0.0001
    
    retracement = (current_price - recovery_low) / total_drop
    
    print(f"\n Recovery Analysis:")
    print(f"   Drop High: {dump_top:.4f}")
    print(f"   Drop Low: {recovery_low:.4f}")
    print(f"   Current: {current_price:.4f}")
    print(f"   Retracement: {retracement*100:.1f}%")
    
    # 4. Tactical Plan (How to Exploit)
    print("\n️ EXPLOITATION STRATEGY:")
    
    if retracement < 0.382:
        print("    BEAR FLAG (Weak Bounce): Best for CONTINUATION SHORT.")
        print(f"      Entry: Break of {recovery_low:.4f}")
        
    elif 0.382 <= retracement <= 0.618:
        print("    DEAD CAT BOUNCE (Normal): Look for Rejection.")
        print(f"      Target Zone: {recovery_low + (total_drop*0.5):.4f} - {recovery_low + (total_drop*0.618):.4f}")
        print("      Action: Limit Sell in this zone with tight SL above 0.618.")
        
    elif retracement > 0.618:
        print("    V-SHAPE RECOVERY (Strong Buyers): Shorts are trapped.")
        print("      Action: DO NOT SHORT yet. Wait for re-test of highs or Long the pullback.")
        print(f"      Current State: {retracement*100:.1f}% recovered. Dangerous for Bears.")
        
    # Volume Profile Check (Simplified)
    avg_vol = df['volume'].mean()
    current_vol = post_dump['volume'].mean()
    
    print(f"\n   Volume Check: Post-Dump Vol ({current_vol:.0f}) vs Avg ({avg_vol:.0f})")
    if current_vol < avg_vol:
        print("   ️ Low Volume Recovery: Likely a Trap (Fakeout). Shorts might re-enter.")
    else:
        print("    High Volume Recovery: Real Buying Interest.")

if __name__ == "__main__":
    study_dump_mechanics()
