import sys
import os
import time

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport

def analyze_sentiment():
    transport = BackpackTransport()
    print("\n GLOBAL SENTIMENT MONITOR (ON-CHAIN BACKPACK DATA)")
    print("=" * 80)
    
    # 1. Fetch Tickers (inclui Funding Rate e Volume)
    tickers = transport.get_funding_rates() # Reused method for tickers
    
    if not tickers:
        print(" Failed to fetch market data.")
        return

    # Metrics
    total_volume_24h = 0
    avg_funding_rate = 0
    high_funding_count = 0 # Bullish Leverage
    neg_funding_count = 0  # Bearish Leverage
    
    ticker_count = 0
    
    # Analyze
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'FUNDING(1h)':<12} | {'24h VOL':<15} | {'SENTIMENT'}")
    print("-" * 80)
    
    sorted_tickers = sorted(tickers, key=lambda x: float(x.get('volume', 0)), reverse=True)
    
    for t in sorted_tickers[:15]: # Top 15 by Volume
        symbol = t.get('symbol')
        if not symbol.endswith('_PERP'): continue
        
        last_price = float(t.get('lastPrice', 0))
        volume = float(t.get('volume', 0))
        # Funding rate might be named differently? 'fundingRate'?
        # Backpack API often returns funding rate as 'fundingRate' or similar
        # Let's assume 'fundingRate' exists.
        funding = float(t.get('fundingRate', 0))
        
        total_volume_24h += volume
        avg_funding_rate += funding
        ticker_count += 1
        
        if funding > 0.0001: # > 0.01% per hour (High)
            high_funding_count += 1
            sentiment = " LEVERAGED LONG"
        elif funding < 0:
            neg_funding_count += 1
            sentiment = " LEVERAGED SHORT"
        else:
            sentiment = "️ NEUTRAL"
            
        print(f"{symbol:<15} | {last_price:<10.4f} | {funding*100:<11.4f}% | ${volume:<14.0f} | {sentiment}")
        
    print("-" * 80)
    
    # Global Metrics
    if ticker_count > 0:
        avg_funding_rate /= ticker_count
        
    print(f" MARKET METRICS:")
    print(f"   Avg Funding Rate: {avg_funding_rate*100:.6f}% (Hourly)")
    print(f"   Long Heavy Mkts:  {high_funding_count}")
    print(f"   Short Heavy Mkts: {neg_funding_count}")
    
    global_signal = "NEUTRAL"
    if avg_funding_rate > 0.00015:
        global_signal = "OVERHEATED (Long Squeeze Risk)"
    elif avg_funding_rate < -0.00005:
        global_signal = "OVERSOLD (Short Squeeze Potential)"
        
    print(f"    GLOBAL SIGNAL: {global_signal}")

if __name__ == "__main__":
    analyze_sentiment()
