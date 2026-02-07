
import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
indicators = BackpackIndicators()

def backtest_strategy(symbol, strategy_type="TREND"):
    print(f"\n SIMULATION: Testing {strategy_type} on {symbol} (48h)...")
    
    # Fetch 48h of 1h data (approx 48 candles)
    klines = data.get_klines(symbol, interval="1h", limit=48)
    if not klines:
        print("   No data found.")
        return 0
        
    df = pd.DataFrame(klines)
    cols = ['open', 'high', 'low', 'close', 'volume']
    for col in cols:
        df[col] = df[col].astype(float)
        
    # Indicators
    bb = indicators.calculate_bollinger_bands(df)
    df['ema_short'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_long'] = df['close'].ewm(span=21, adjust=False).mean()
    df['upper'] = bb['upper']
    df['lower'] = bb['lower']
    
    # Simulation Loop
    balance = 100
    position = 0 # 0 = None, 1 = Long, -1 = Short
    entry_price = 0
    trades = 0
    wins = 0
    
    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        prev_price = df['close'].iloc[i-1]
        
        # Strategy Logic
        signal = 0
        if strategy_type == "TREND":
            # Golden Cross / Death Cross
            if df['ema_short'].iloc[i] > df['ema_long'].iloc[i] and df['ema_short'].iloc[i-1] <= df['ema_long'].iloc[i-1]:
                signal = 1 # Buy
            elif df['ema_short'].iloc[i] < df['ema_long'].iloc[i] and df['ema_short'].iloc[i-1] >= df['ema_long'].iloc[i-1]:
                signal = -1 # Sell
                
        elif strategy_type == "MEAN_REVERSION":
            # BB Bounce
            if price < df['lower'].iloc[i]:
                signal = 1 # Buy (Oversold)
            elif price > df['upper'].iloc[i]:
                signal = -1 # Sell (Overbought)
        
        # Execution
        if position == 0:
            if signal == 1:
                position = 1
                entry_price = price
                # print(f"  🟢 LONG at {price:.4f}")
            elif signal == -1:
                position = -1
                entry_price = price
                # print(f"   SHORT at {price:.4f}")
        
        elif position == 1:
            if signal == -1: # Close Long
                pnl = (price - entry_price) / entry_price
                balance *= (1 + pnl)
                position = 0
                trades += 1
                if pnl > 0: wins += 1
                # print(f"  Exit Long at {price:.4f} | PnL: {pnl*100:.2f}%")
                
        elif position == -1:
            if signal == 1: # Close Short
                pnl = (entry_price - price) / entry_price
                balance *= (1 + pnl)
                position = 0
                trades += 1
                if pnl > 0: wins += 1
                # print(f"  Exit Short at {price:.4f} | PnL: {pnl*100:.2f}%")
                
    # Force Close at end
    if position != 0:
        price = df['close'].iloc[-1]
        if position == 1:
            pnl = (price - entry_price) / entry_price
        else:
            pnl = (entry_price - price) / entry_price
        balance *= (1 + pnl)
        trades += 1
        if pnl > 0: wins += 1
        
    roi = (balance - 100)
    win_rate = (wins/trades * 100) if trades > 0 else 0
    print(f"   RESULT: ROI {roi:.2f}% | Trades: {trades} | Win Rate: {win_rate:.0f}%")
    return roi

def run_weekly_simulation():
    print(" RUNNING SCIENTIFIC VALIDATION FOR WEEKLY MODEL")
    print("=" * 60)
    
    # Candidates from Market Scan
    candidates = ['IP_USDC_PERP', 'BERA_USDC_PERP', 'PENGU_USDC_PERP', 'FOGO_USDC_PERP']
    
    scores = {}
    
    for symbol in candidates:
        print(f"\nAnalyzing {symbol}...")
        
        # Test Trend Strategy
        roi_trend = backtest_strategy(symbol, "TREND")
        
        # Test Mean Reversion Strategy
        roi_mean = backtest_strategy(symbol, "MEAN_REVERSION")
        
        # Verdict Logic
        if roi_trend > roi_mean and roi_trend > 0:
            verdict = "TREND_FOLLOWING"
            confidence = "HIGH" if roi_trend > 5 else "MEDIUM"
        elif roi_mean > roi_trend and roi_mean > 0:
            verdict = "MEAN_REVERSION"
            confidence = "HIGH" if roi_mean > 5 else "MEDIUM"
        else:
            verdict = "AVOID / CHOPPY"
            confidence = "LOW"
            
        scores[symbol] = {
            "verdict": verdict,
            "best_roi": max(roi_trend, roi_mean),
            "confidence": confidence
        }
        
    print("\n\n FINAL WEEKLY VERDICT (DATA-DRIVEN)")
    print("=" * 60)
    for symbol, data in scores.items():
        print(f" {symbol}: {data['verdict']} (Confidence: {data['confidence']}) | Exp. Return: {data['best_roi']:.2f}%")

if __name__ == "__main__":
    run_weekly_simulation()
