import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

def money_flow_radar():
    print("\n [MONEY FLOW RADAR] Scanning On-Chain Capital Flows...")
    
    # Init
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # 1. Get All Tickers
    tickers = data.get_tickers()
    if not tickers:
        print("    Failed to fetch tickers.")
        return

    # 2. Process Data
    # Structure of ticker: {'symbol': 'SOL_USDC', 'firstPrice': ..., 'lastPrice': ..., 'volume': ..., 'quoteVolume': ...}
    # We want 'quoteVolume' (USDC Volume) as proxy for Money Flow.
    
    market_data = []
    for t in tickers:
        symbol = t.get('symbol')
        if not symbol.endswith('_PERP'): continue # Focus on Perps for Leverage
        
        # Exclude stablecoin pairs if any (e.g. USDC_USDT)
        
        quote_vol = float(t.get('quoteVolume', 0))
        price_change = float(t.get('priceChangePercent', 0))
        last_price = float(t.get('lastPrice', 0))
        
        market_data.append({
            'symbol': symbol,
            'volume_usdc': quote_vol,
            'price_change_24h': price_change,
            'price': last_price
        })
        
    # 3. Sort by Money Flow (Volume)
    df = pd.DataFrame(market_data)
    df = df.sort_values(by='volume_usdc', ascending=False)
    
    print(f"\n TOP 10 ASSETS BY CAPITAL INFLOW (24H):")
    print(f"{'RANK':<4} | {'SYMBOL':<15} | {'FLOW (USDC)':<15} | {'24H %':<8} | {'PRICE'}")
    print("-" * 65)
    
    top_assets = []
    
    for i in range(min(15, len(df))):
        row = df.iloc[i]
        rank = i + 1
        vol_fmt = f"${row['volume_usdc']:,.0f}"
        pct_fmt = f"{row['price_change_24h']:+.2f}%"
        
        # Highlight "Hot" assets (Positive Flow + High Volume)
        hot_tag = "" if row['price_change_24h'] > 5.0 else ""
        
        print(f"{rank:<4} | {row['symbol']:<15} | {vol_fmt:<15} | {pct_fmt:<8} | {row['price']:.4f} {hot_tag}")
        
        if rank <= 10:
            top_assets.append(row['symbol'])

    print("-" * 65)
    
    # Suggest Updates
    print("\n SUGGESTED HUNTER KILLER TARGETS:")
    current_targets = [
        "SOL_USDC_PERP", "ETH_USDC_PERP", "SUI_USDC_PERP", 
        "DOGE_USDC_PERP", "AVAX_USDC_PERP", "LINK_USDC_PERP", "JUP_USDC_PERP"
    ]
    
    new_targets = [t for t in top_assets if t not in current_targets and t != "BTC_USDC_PERP"]
    
    if new_targets:
        print(f"    Found {len(new_targets)} new High-Flow Assets: {new_targets}")
        print("   -> Recommended Action: Add to Hunter Killer list.")
    else:
        print("    Current Hunter Killer list covers top flows.")

if __name__ == "__main__":
    money_flow_radar()
