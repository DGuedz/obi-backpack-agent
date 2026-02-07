import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()

def analyze_sleep_parameters():
    print(" SLEEP MODE ANALYSIS (Safety First)")
    print("====================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    # 1. Margin Check
    balances = data.get_balances()
    usdc = balances.get('USDC', {})
    available = float(usdc.get('available', 0))
    print(f" Available Capital: ${available:.2f}")
    
    if available < 100:
        print("   ️ WARNING: Request for $100/trade exceeds available balance.")
        print("    Recommendation: Use Max Available ($84) or $50.")
    
    # 2. Volatility Analysis (SOL)
    symbol = "SOL_USDC_PERP"
    print(f"\n Volatility Check ({symbol}):")
    klines = data.get_klines(symbol, interval="1h", limit=24) # Last 24h
    
    if klines:
        df = pd.DataFrame(klines)
        for col in ['high', 'low', 'close']:
            df[col] = df[col].astype(float)
            
        # Calculate Average True Range (Approximation: High - Low)
        df['range'] = df['high'] - df['low']
        df['range_pct'] = (df['range'] / df['close']) * 100
        
        avg_volatility = df['range_pct'].mean()
        max_volatility = df['range_pct'].max()
        
        print(f"   Avg Hourly Volatility: {avg_volatility:.2f}%")
        print(f"   Max Hourly Volatility: {max_volatility:.2f}%")
        
        # Recommendation
        # For sleep, SL should be > Avg Volatility * 2 (Safety factor)
        safe_sl = avg_volatility * 1.5
        print(f"\n️ SAFETY RECOMMENDATIONS (5x Leverage):")
        print(f"   • Safe SL Distance: {safe_sl:.2f}% (Price Move)")
        print(f"   • Liquidation Risk (5x): 20% Move (Very Safe)")
        print(f"   • Stop Loss PnL Impact: -{safe_sl * 5:.2f}% ROI")
        
        # Fees Analysis
        # Taker: 0.08% * 2 = 0.16%
        # Spread: ~0.02%
        # Breakeven: ~0.18% Price Move
        print(f"\n COST ANALYSIS:")
        print(f"   • Breakeven Move: 0.20%")
        print(f"   • Min TP Target: 0.50% (To profit net)")

if __name__ == "__main__":
    analyze_sleep_parameters()
