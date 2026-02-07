import time
import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

# --- CONFIG ---
TARGET_LEVERAGE = 50
MIN_VOLUME_USDC = 2_000_000 # Minimum 2M volume for liquidity safety at 50x
RSI_OVERSOLD = 25
RSI_OVERBOUGHT = 75

def recovery_scanner_50x():
    print(f"\n️ [RECOVERY SCANNER 50X] HIGH LEVERAGE OPPORTUNITY SEEKER")
    print("   ️ WARNING: 50x Leverage requires SURGICAL precision.")
    print("    Criteria: Extreme RSI + High Volatility + High Liquidity")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    # 1. Get All Tickers
    print("\n    Scanning Market for 50x Candidates...")
    tickers = data.get_tickers()
    if not tickers:
        print("    Failed to fetch tickers.")
        return

    perp_tickers = [t for t in tickers if t['symbol'].endswith('_PERP')]
    
    candidates = []
    
    print(f"\n   {'SYMBOL':<15} | {'RSI (15m)':<10} | {'VOL (24h)':<12} | {'CHANGE':<8} | {'STATUS'}")
    print("-" * 75)
    
    for t in perp_tickers:
        symbol = t['symbol']
        quote_vol = float(t.get('quoteVolume', 0))
        
        # Filter: Liquidity
        if quote_vol < MIN_VOLUME_USDC: continue
        
        try:
            # Get 15m Candles (Standard Scalp Timeframe)
            candles = data.get_klines(symbol, "15m", limit=50)
            if not candles or len(candles) < 50: continue
            
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            rsi = indicators.calculate_rsi(df).iloc[-1]
            change = float(t['priceChangePercent'])
            
            status = ""
            signal = None
            
            # Setup 1: Extreme Oversold Bounce (Long)
            if rsi < RSI_OVERSOLD:
                status = "🟢 LONG (Oversold)"
                signal = "Buy"
            
            # Setup 2: Extreme Overbought Dump (Short)
            elif rsi > RSI_OVERBOUGHT:
                status = " SHORT (Overbought)"
                signal = "Sell"
                
            # Setup 3: Momentum Crash (Flash Scalper Logic integration)
            # If dropping hard > -3% and RSI not yet oversold (room to fall)
            elif change < -3.0 and rsi > 30:
                status = " MOMENTUM SHORT"
                signal = "Sell"
                
            if status:
                vol_str = f"${quote_vol/1_000_000:.1f}M"
                print(f"   {symbol:<15} | {rsi:<10.2f} | {vol_str:<12} | {change:>+6.2f}%   | {status}")
                
                candidates.append({
                    'symbol': symbol,
                    'rsi': rsi,
                    'vol': quote_vol,
                    'status': status,
                    'signal': signal,
                    'price': float(t['lastPrice'])
                })
                
        except Exception as e:
            continue
            
    print("-" * 75)
    
    if not candidates:
        print("\n    No 50x setups found matching strict criteria.")
        return
        
    # Sort by 'juiciness' (Extreme RSI deviation from 50)
    candidates.sort(key=lambda x: abs(x['rsi'] - 50), reverse=True)
    
    print("\n TOP 3 RECOVERY OPPORTUNITIES (50X APPROVED):")
    for i, c in enumerate(candidates[:3]):
        print(f"   {i+1}. {c['symbol']} -> {c['status']} (RSI: {c['rsi']:.2f})")
        
    print("\n️ WAITING FOR USER APPROVAL TO EXECUTE...")
    print("   To execute, please confirm which asset (1, 2, or 3) or 'ALL'.")

if __name__ == "__main__":
    recovery_scanner_50x()
