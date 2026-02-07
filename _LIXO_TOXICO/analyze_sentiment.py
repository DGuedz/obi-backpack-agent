import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def analyze_market_sentiment():
    print(" ANALYZING MARKET SENTIMENT (7H PROJECTION)")
    print("===========================================")
    
    # 1. Backpack Internal Sentiment (Funding & Advance/Decline)
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    try:
        tickers = data.get_tickers()
        df = pd.DataFrame(tickers)
        
        # Convert numeric columns
        cols = ['lastPrice', 'priceChangePercent', 'volume', 'quoteVolume']
        for c in cols:
            df[c] = df[c].astype(float)
            
        # Filter Liquid Pairs (> $1M Vol)
        liquid_df = df[df['quoteVolume'] > 1_000_000]
        
        # Advance/Decline Ratio
        advancers = len(liquid_df[liquid_df['priceChangePercent'] > 0])
        decliners = len(liquid_df[liquid_df['priceChangePercent'] < 0])
        ratio = advancers / decliners if decliners > 0 else float('inf')
        
        print(f"\n[BACKPACK INTERNAL]")
        print(f"   Advancers: {advancers} | Decliners: {decliners}")
        print(f"   A/D Ratio: {ratio:.2f}")
        
        if ratio > 1.5:
            print("    Sentiment: BULLISH (Broad Participation)")
        elif ratio < 0.6:
            print("    Sentiment: BEARISH (Broad Weakness)")
        else:
            print("    Sentiment: NEUTRAL/MIXED (Stock Picker's Market)")
            
        # Top Gainers (Momentum)
        print("\n    Top Gainers (24h):")
        top_gainers = liquid_df.sort_values(by='priceChangePercent', ascending=False).head(3)
        for _, row in top_gainers.iterrows():
            print(f"      {row['symbol']}: +{row['priceChangePercent']}%")
            
    except Exception as e:
        print(f" Error analyzing Backpack data: {e}")

    # 2. External Sentiment (CMC/Global)
    # Using WebSearch for "Live" sentiment is better if API key is missing or basic.
    # But code cannot call tools directly. The Agent does. 
    # Here we just print a placeholder or try a public endpoint if available.
    # We will rely on the Agent's WebSearch tool for the "CMC" part in the final report.
    print("\n[EXTERNAL/CMC DATA]")
    print("   (Fetching via Web Search in next step...)")

if __name__ == "__main__":
    analyze_market_sentiment()
