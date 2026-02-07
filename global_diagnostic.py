
import os
import sys
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from technical_oracle import MarketProxyOracle

def diagnose_market():
    print(" INITIATING GLOBAL MARKET DIAGNOSTIC (AEGIS COMPLIANT)...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # 1. Fetch all Perps
    tickers = data.get_tickers()
    perps = [t for t in tickers if t['symbol'].endswith('_PERP')]
    
    print(f"    Scanning {len(perps)} Assets...")
    
    opportunities = []
    
    for t in perps:
        symbol = t['symbol']
        price = float(t['lastPrice'])
        vol = float(t.get('quoteVolume', 0))
        
        if vol < 500000: continue # Liquidity Filter
        
        try:
            # 2. Macro Trend Check (1h)
            klines = data.get_klines(symbol, "1h", limit=60)
            if not klines: continue
            
            closes = pd.Series([float(k['close']) for k in klines])
            ema50 = closes.ewm(span=50, adjust=False).mean().iloc[-1]
            
            trend = "BULLISH" if price > ema50 else "BEARISH"
            dist_ema = ((price - ema50) / ema50) * 100
            
            # 3. Micro RSI Check (15m)
            klines_15m = data.get_klines(symbol, "15m", limit=20)
            closes_15m = pd.Series([float(k['close']) for k in klines_15m])
            delta = closes_15m.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 4. Oracle Narrative (Only for interesting ones)
            if (trend == "BULLISH" and rsi < 45) or (trend == "BEARISH" and rsi > 55):
                oracle = MarketProxyOracle(symbol, auth, data)
                narrative = oracle.get_market_narrative()
                obi = narrative['obi'] if narrative else 0
                
                opportunities.append({
                    'symbol': symbol,
                    'price': price,
                    'trend': trend,
                    'dist_ema': dist_ema,
                    'rsi': rsi,
                    'obi': obi,
                    'vol': vol
                })
                
        except Exception as e:
            continue
            
    # 5. Report
    print("\n MARKET HEALTH REPORT:")
    bulls = len([o for o in opportunities if o['trend'] == "BULLISH"])
    bears = len([o for o in opportunities if o['trend'] == "BEARISH"])
    print(f"    Bullish Trend Assets: {bulls}")
    print(f"    Bearish Trend Assets: {bears}")
    
    if bears > bulls:
        print("   ️ MACRO SENTIMENT: RISK OFF (Bear Dominance). Cash is King.")
    else:
        print("    MACRO SENTIMENT: RISK ON (Bull Dominance). Look for dips.")
        
    print("\n TOP CONFLUENCE OPPORTUNITIES (AEGIS APPROVED):")
    # Sort by Confluence Score (RSI dip + OBI support)
    # For Longs: Low RSI + Positive OBI
    long_candidates = [o for o in opportunities if o['trend'] == "BULLISH" and o['rsi'] < 40 and o['obi'] > 0.1]
    short_candidates = [o for o in opportunities if o['trend'] == "BEARISH" and o['rsi'] > 60 and o['obi'] < -0.1]
    
    if not long_candidates and not short_candidates:
        print("    No AEGIS-Compliant setups found. Market is choppy or extended.")
    
    for c in long_candidates:
        print(f"   🟢 LONG: {c['symbol']} | Price: {c['price']} | RSI: {c['rsi']:.1f} | OBI: {c['obi']:.2f} | EMA Dist: {c['dist_ema']:.2f}%")
        
    for c in short_candidates:
        print(f"    SHORT: {c['symbol']} | Price: {c['price']} | RSI: {c['rsi']:.1f} | OBI: {c['obi']:.2f} | EMA Dist: {c['dist_ema']:.2f}%")

if __name__ == "__main__":
    diagnose_market()
