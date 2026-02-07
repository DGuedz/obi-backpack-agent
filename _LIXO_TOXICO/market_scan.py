
import os
import sys
import json
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def fetch_market_intelligence():
    print(" Fetching Market Intelligence...")
    
    # 1. Tickers (Price, Volume, Change)
    tickers = data.get_tickers()
    
    # 2. Market Markets (to filter for perps)
    markets = data.get_markets()
    
    # Filter for USDT/USDC Perps
    perp_markets = [m for m in markets if 'PERP' in m['symbol']]
    
    print(f" Analyzed {len(perp_markets)} Perpetual Markets.")
    
    # Analyze Top Opportunities based on Volatility and Volume
    market_data = []
    for ticker in tickers:
        symbol = ticker.get('symbol')
        if 'PERP' not in symbol:
            continue
            
        # Extract metrics (Backpack API structure might vary, adapting to common keys)
        # Usually ticker has 'lastPrice', 'volume', 'priceChangePercent'
        # Let's inspect one ticker structure in the output to be sure, 
        # but for now I'll store the whole thing and process in the print.
        market_data.append(ticker)
        
    # Sort by Volume (Liquidity)
    market_data.sort(key=lambda x: float(x.get('volume', 0)), reverse=True)
    
    top_3_vol = market_data[:3]
    print("\n Top 3 Volume Leaders:")
    for m in top_3_vol:
        print(f"  {m['symbol']}: Vol {m.get('quoteVolume', m.get('volume'))} | Price {m['lastPrice']} | Change {m.get('priceChangePercent', 'N/A')}%")

    # Sort by Volatility (Change)
    market_data.sort(key=lambda x: abs(float(x.get('priceChangePercent', 0))), reverse=True)
    
    top_3_volat = market_data[:3]
    print("\n Top 3 Volatility Movers:")
    for m in top_3_volat:
        print(f"  {m['symbol']}: Change {m.get('priceChangePercent')}% | Price {m['lastPrice']}")

    return top_3_vol, top_3_volat

if __name__ == "__main__":
    fetch_market_intelligence()
