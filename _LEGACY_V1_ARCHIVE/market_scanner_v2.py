import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

def scan_all_markets():
    print("\n️ [FULL MARKET SCAN] ANALYZING ALL ASSETS FOR RECOVERY...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    tickers = data.get_tickers()
    if not tickers: return
    
    opportunities = []
    
    print(f"\n   {'SYMBOL':<15} | {'RSI':<6} | {'VOL':<10} | {'CHANGE':<8} | {'SETUP'}")
    print("-" * 65)
    
    for t in tickers:
        symbol = t['symbol']
        if not symbol.endswith('_PERP'): continue
        
        # IGNORE VOLUME FILTER - SCAN EVERYTHING
        quote_vol = float(t.get('quoteVolume', 0))
        change = float(t.get('priceChangePercent', 0))
        
        try:
            # 15m Timeframe for Faster Scalps
            candles = data.get_klines(symbol, "15m", limit=50)
            if not candles: continue
            
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            rsi = indicators.calculate_rsi(df).iloc[-1]
            
            setup = ""
            
            # 1. OVERSOLD BOUNCE (RSI < 30)
            if rsi < 30:
                setup = "🟢 BUY (Oversold)"
            
            # 2. OVERBOUGHT DUMP (RSI > 70)
            elif rsi > 70:
                setup = " SELL (Overbought)"
                
            # 3. MOMENTUM PUMP (Price up > 5% but RSI not maxed)
            elif change > 5.0 and rsi < 70:
                setup = " CHASE (Momentum)"
                
            # 4. CRASH DUMP (Price down > 5% but RSI not floored)
            elif change < -5.0 and rsi > 30:
                setup = " SHORT (Trend)"
                
            if setup:
                vol_str = f"${quote_vol/1000:.0f}K"
                print(f"   {symbol:<15} | {rsi:<6.2f} | {vol_str:<10} | {change:>+6.2f}%   | {setup}")
                
                opportunities.append({
                    'symbol': symbol,
                    'rsi': rsi,
                    'vol': quote_vol,
                    'setup': setup,
                    'price': float(t['lastPrice'])
                })
                
        except:
            continue
            
    print("-" * 65)
    
    if opportunities:
        # Sort by most extreme RSI deviation from 50
        opportunities.sort(key=lambda x: abs(x['rsi'] - 50), reverse=True)
        
        best = opportunities[0]
        print(f"\n BEST RECOVERY SHOT: {best['symbol']}")
        print(f"    Action: {best['setup']}")
        print(f"    RSI (15m): {best['rsi']:.2f}")
        
        # Risk Warning for Low Vol
        if best['vol'] < 1_000_000:
            print("   ️ WARNING: Low Liquidity. Use Limit Orders Only.")
            
    else:
        print("\n    Market is completely flat. No edge found.")

if __name__ == "__main__":
    scan_all_markets()
