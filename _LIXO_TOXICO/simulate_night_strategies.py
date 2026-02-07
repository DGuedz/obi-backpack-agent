import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()

# --- SIMULATION CONFIG ---
CAPITAL = 1000
LEVERAGE = 10
NOTIONAL = CAPITAL * LEVERAGE # $10,000 Volume
# MAKER FEE ADJUSTMENT
FEE_RATE = 0.0002 # 0.02% Maker (Optimized)
SPREAD_COST = 0.0000 # 0.00% (Maker gets paid spread usually or fills at mid? Let's assume 0 spread cost for limit)
TOTAL_COST_PCT = (FEE_RATE * 2) 

def simulate_strategies():
    print(" SIMULATION: NIGHT OWL (MAKER/POST-ONLY) | 7 HOURS")
    print(f"   Capital: ${CAPITAL} | Lev: {LEVERAGE}x | Vol/Trade: ${NOTIONAL}")
    print(f"   Cost Basis (Maker Fees): {TOTAL_COST_PCT*100:.2f}% per trade")
    print("=======================================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    # 1. Fetch Data (SOL 1m candles for granular sim)
    # 7 hours * 60 mins = 420 candles. Let's fetch 1000.
    symbol = "SOL_USDC_PERP"
    print(f"   Fetching 1000 candles for {symbol} (1m)...")
    klines = data.get_klines(symbol, interval="1m", limit=1000)
    
    if not klines:
        print(" Error fetching data.")
        return

    df = pd.DataFrame(klines)
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
        
    # Calculate Indicators
    df['rsi'] = indicators.calculate_rsi(df) # 14
    bb = indicators.calculate_bollinger_bands(df)
    df['upper'] = bb['upper']
    df['lower'] = bb['lower']
    df['sma'] = bb['middle']
    
    # --- SCENARIO A: THE SNIPER (15m Logic on 1m Data) ---
    # Simplified: RSI < 25 or > 75
    # Since we have 1m data, we can approximate 15m RSI or just use 1m RSI Extreme for scalp.
    # User wants 70 trades. RSI < 25 on 15m happens rarely.
    # Let's test 1m RSI < 20 / > 80.
    
    print("\n SCENARIO A: RSI EXTREME (1m Scalp)")
    trades_a = 0
    wins_a = 0
    gross_profit_a = 0
    
    for i in range(20, len(df)):
        rsi = df['rsi'].iloc[i]
        price = df['close'].iloc[i]
        
        # Entry Logic
        if rsi < 20 or rsi > 80:
            trades_a += 1
            # Simple Outcome: Does it move 0.3% in favor before 0.2% against?
            # Looking ahead 10 candles
            outcome = 0
            entry_price = price
            target = 0.003 # 0.3% move
            stop = 0.002 # 0.2% stop
            
            direction = 1 if rsi < 20 else -1
            
            for j in range(1, 10):
                if i+j >= len(df): break
                future_high = df['high'].iloc[i+j]
                future_low = df['low'].iloc[i+j]
                
                if direction == 1: # Long
                    if future_high >= entry_price * (1+target):
                        outcome = target * NOTIONAL
                        break
                    if future_low <= entry_price * (1-stop):
                        outcome = -stop * NOTIONAL
                        break
                else: # Short
                    if future_low <= entry_price * (1-target):
                        outcome = target * NOTIONAL
                        break
                    if future_high >= entry_price * (1+stop):
                        outcome = -stop * NOTIONAL
                        break
            
            if outcome > 0: wins_a += 1
            gross_profit_a += outcome
            
    # --- SCENARIO B: BOLLINGER BAND HARVESTER (Mean Reversion) ---
    # Buy Lower Band, Sell Upper Band
    print(" SCENARIO B: BOLLINGER HARVESTER (1m Grid)")
    trades_b = 0
    wins_b = 0
    gross_profit_b = 0
    
    for i in range(20, len(df)):
        price = df['close'].iloc[i]
        lower = df['lower'].iloc[i]
        upper = df['upper'].iloc[i]
        
        # Touch Lower Band -> Long
        if price <= lower:
            trades_b += 1
            # Target: SMA. Stop: 0.3% below.
            target_price = df['sma'].iloc[i] # Dynamic target? No, snapshot at entry.
            # Optimized: 0.4% Profit / 0.3% Stop
            target = 0.004
            stop = 0.003
            
            outcome = 0
            for j in range(1, 10):
                if i+j >= len(df): break
                future_high = df['high'].iloc[i+j]
                future_low = df['low'].iloc[i+j]
                
                if future_high >= price * (1+target):
                    outcome = target * NOTIONAL
                    break
                if future_low <= price * (1-stop):
                    outcome = -stop * NOTIONAL
                    break
            
            if outcome > 0: wins_b += 1
            gross_profit_b += outcome

        # Touch Upper Band -> Short
        elif price >= upper:
            trades_b += 1
            target = 0.004
            stop = 0.003
            outcome = 0
            for j in range(1, 10):
                if i+j >= len(df): break
                future_low = df['low'].iloc[i+j]
                future_high = df['high'].iloc[i+j]
                
                if future_low <= price * (1-target):
                    outcome = target * NOTIONAL
                    break
                if future_high >= price * (1+stop):
                    outcome = -stop * NOTIONAL
                    break
            
            if outcome > 0: wins_b += 1
            gross_profit_b += outcome

    # --- RESULTS ---
    # Calc Fees
    fees_a = trades_a * (NOTIONAL * TOTAL_COST_PCT)
    net_a = gross_profit_a - fees_a
    
    fees_b = trades_b * (NOTIONAL * TOTAL_COST_PCT)
    net_b = gross_profit_b - fees_b
    
    print("\n RESULTS (Last ~16 Hours Data):")
    print(f"   [A] SNIPER (RSI Extreme):")
    print(f"       Trades: {trades_a}")
    print(f"       Win Rate: {wins_a/trades_a:.1%} ({wins_a}/{trades_a})")
    print(f"       Fees Paid: ${fees_a:.2f}")
    print(f"       NET PROFIT: ${net_a:.2f}")
    
    print(f"\n   [B] HARVESTER (Bollinger):")
    print(f"       Trades: {trades_b}")
    print(f"       Win Rate: {wins_b/trades_b:.1%} ({wins_b}/{trades_b})")
    print(f"       Fees Paid: ${fees_b:.2f}")
    print(f"       NET PROFIT: ${net_b:.2f}")
    
    print("\n VERDICT:")
    if net_b > net_a and trades_b >= 50:
        print("    HARVESTER is the choice for Volume (70+ trades) + Profit.")
    elif net_a > net_b:
        print("   ️ SNIPER is more profitable but Lower Volume.")
    else:
        print("    Both strategies struggling with Fees. Need TIGHTER SPREAD or MAKER ORDERS.")

if __name__ == "__main__":
    simulate_strategies()
