import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

def deep_sniper_scan():
    print("\n [DEEP SNIPER] SCANNING FOR 20X OPPORTUNITIES...")
    print("    Criteria: Extreme RSI + Volume Spike + Trend Alignment")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    # 1. Get Tickers
    tickers = data.get_tickers()
    if not tickers: return
    
    candidates = []
    
    print(f"\n   {'SYMBOL':<15} | {'RSI (1h)':<8} | {'VOL (24h)':<12} | {'CHANGE':<8} | {'SIGNAL'}")
    print("-" * 65)
    
    for t in tickers:
        symbol = t['symbol']
        if not symbol.endswith('_PERP'): continue
        
        # Filter Low Volume (Risk of manipulation/slippage)
        quote_vol = float(t.get('quoteVolume', 0))
        if quote_vol < 5_000_000: continue # Min $5M Volume
        
        # Get Candles for RSI
        try:
            candles = data.get_klines(symbol, "1h", limit=50)
            if not candles: continue
            
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            rsi = indicators.calculate_rsi(df).iloc[-1]
            price_change = float(t.get('priceChangePercent', 0))
            
            signal = ""
            
            # SHORT Opportunities (Overbought in Bear Market)
            if rsi > 70 and price_change > 5.0:
                signal = " SHORT (Pump & Dump?)"
            
            # LONG Opportunities (Oversold Bounce)
            elif rsi < 25 and price_change < -5.0:
                signal = "🟢 LONG (Oversold Bounce)"
                
            # Trend Continuation (Strong Momentum)
            elif price_change < -10.0:
                signal = " CRASH (Follow Trend?)"
                
            if signal:
                print(f"   {symbol:<15} | {rsi:<8.2f} | ${quote_vol/1_000_000:.1f}M      | {price_change:>+6.2f}%   | {signal}")
                candidates.append({
                    'symbol': symbol, 
                    'rsi': rsi, 
                    'vol': quote_vol, 
                    'change': price_change,
                    'signal': signal
                })
                
        except:
            continue
            
    print("-" * 65)
    
    # Recommendation Logic
    if candidates:
        # Prioritize High Volume + Extreme RSI
        best_pick = sorted(candidates, key=lambda x: x['vol'], reverse=True)[0]
        
        print(f"\n GOLDEN TARGET IDENTIFIED: {best_pick['symbol']}")
        print(f"    Reason: {best_pick['signal']}")
        print(f"    RSI: {best_pick['rsi']:.2f}")
        print(f"    Volume: ${best_pick['vol']:,.0f}")
        
        if "SHORT" in best_pick['signal'] or "CRASH" in best_pick['signal']:
             print("\n    STRATEGY: 20x SHORT. Enter on pullback to VWAP.")
        else:
             print("\n    STRATEGY: 20x LONG. Enter on support confirmation.")
             
    else:
        print("\n    No 'Perfect' 20x Setups found right now. Market is choppy.")

if __name__ == "__main__":
    deep_sniper_scan()
