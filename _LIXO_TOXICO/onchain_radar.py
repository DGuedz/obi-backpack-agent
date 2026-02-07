
import os
import sys
import time
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def radar_sweep():
    print(" ON-CHAIN RADAR: Scanning for Capital Rotation...")
    print("==================================================")
    
    # 1. Get All Tickers
    tickers = data.get_tickers()
    if not tickers:
        print(" API Error: No tickers.")
        return

    # 2. Filter & Sort by 24h Volatility and Volume
    candidates = []
    for t in tickers:
        symbol = t['symbol']
        if "PERP" not in symbol: continue
        
        price = float(t['lastPrice'])
        change = float(t['priceChangePercent'])
        volume = float(t['quoteVolume']) # USD Volume
        
        candidates.append({
            'symbol': symbol,
            'change': change,
            'volume': volume,
            'price': price
        })
        
    # Sort by Volume (Liquidity)
    top_vol = sorted(candidates, key=lambda x: x['volume'], reverse=True)[:5]
    
    # Sort by Change (Volatility)
    top_gainers = sorted(candidates, key=lambda x: x['change'], reverse=True)[:5]
    top_losers = sorted(candidates, key=lambda x: x['change'])[:5]
    
    print("\n LIQUIDITY MAGNETS (Where the whales are):")
    for c in top_vol:
        print(f"   {c['symbol']}: ${c['volume']/1000000:.1f}M | {c['change']:.2f}%")
        
    print("\n PUMP RADAR (Capital Inflow):")
    for c in top_gainers:
        print(f"   {c['symbol']}: +{c['change']:.2f}% | Vol: ${c['volume']/1000:.0f}k")
        
    print("\n DUMP RADAR (Capital Outflow):")
    for c in top_losers:
        print(f"   {c['symbol']}: {c['change']:.2f}% | Vol: ${c['volume']/1000:.0f}k")
        
    # 3. Correlation Insight
    # If BTC/ETH are flat but Alts are pumping -> Altseason Rotation
    # If everything is red -> Risk Off (Cash is King)
    
    btc = next((c for c in candidates if 'BTC' in c['symbol']), None)
    if btc:
        print(f"\n MARKET CONTEXT (BTC): {btc['change']:.2f}%")
        
        if -1 < btc['change'] < 1:
            print("    BTC Stable. Look for Alt Rotation in Top Gainers.")
        elif btc['change'] < -2:
            print("   ️ BTC Dumping. High Risk for Longs. Look for Shorts in Weak Alts.")
        elif btc['change'] > 2:
            print("   🟢 BTC Pumping. A rising tide lifts all boats.")

if __name__ == "__main__":
    while True:
        radar_sweep()
        time.sleep(30) # Scan every 30s
