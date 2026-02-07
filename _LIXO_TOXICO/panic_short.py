import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# --- CONFIG ---
TARGET_SHORT_SIZE = 1000.0 # Notional per Short
MAX_SHORTS = 3

def panic_short_revenge():
    print("\n [PANIC SHORT] REVENGE PROTOCOL ACTIVATED")
    print("    Objective: Catch the Crash & Recover Losses.")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Identify Weakest Assets (Biggest Losers)
    print("    Scanning for Weakest Links...")
    tickers = data.get_tickers()
    if not tickers: return
    
    losers = []
    for t in tickers:
        symbol = t['symbol']
        if not symbol.endswith('_PERP'): continue
        change = float(t.get('priceChangePercent', 0))
        losers.append({'symbol': symbol, 'change': change, 'price': float(t['lastPrice'])})
        
    # Sort by biggest drop (Momentum is Down)
    losers.sort(key=lambda x: x['change'])
    
    top_shorts = losers[:5]
    print(f"    Top 5 Losers: {[x['symbol'] for x in top_shorts]}")
    
    # 2. Execute Shorts (Market Orders - No Mercy)
    print("   ️ Executing Revenge Shorts...")
    
    executed = 0
    for asset in top_shorts:
        if executed >= MAX_SHORTS: break
        
        symbol = asset['symbol']
        price = asset['price']
        
        # Calculate Quantity
        qty = TARGET_SHORT_SIZE / price
        qty = round(qty, 2)
        if 'ETH' in symbol: qty = round(qty, 3)
        if 'BTC' in symbol: qty = round(qty, 4)
        
        try:
            print(f"      -> SHORTING {symbol} ({qty} units)...")
            res = trade.execute_order(symbol, "Ask", 0, qty, order_type="Market")
            
            if res:
                print(f"          Short Opened on {symbol}")
                executed += 1
            else:
                print(f"          Failed to Short {symbol} (Margin?)")
                
        except Exception as e:
            print(f"         ️ Error: {e}")
            
    print("\n   ️ Note: This is high risk. Monitor closely.")

if __name__ == "__main__":
    panic_short_revenge()
