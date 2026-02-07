import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

load_dotenv()

def check_trend():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    targets = ["SOL_USDC_PERP", "ETH_USDC_PERP", "BTC_USDC_PERP"]
    
    print("\n TREND CHECK (1h Timeframe)")
    print("=" * 50)
    
    for symbol in targets:
        klines = data.get_klines(symbol, "1h", limit=100)
        if not klines: continue
        
        df = pd.DataFrame(klines)
        for col in ['close', 'high', 'low', 'open', 'volume']:
            df[col] = df[col].astype(float)
            
        # EMAs
        df['ema_50'] = df['close'].ewm(span=50).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()
        
        current_price = df['close'].iloc[-1]
        ema_50 = df['ema_50'].iloc[-1]
        ema_20 = df['ema_20'].iloc[-1]
        
        trend = "NEUTRAL"
        if current_price > ema_50:
            trend = "BULLISH (UP)"
        else:
            trend = "BEARISH (DOWN)"
            
        strength = "WEAK"
        if abs(current_price - ema_50) / ema_50 > 0.01:
            strength = "STRONG"
            
        print(f"{symbol}: {trend} ({strength})")
        print(f"   Price: {current_price:.2f} | EMA 50: {ema_50:.2f} | EMA 20: {ema_20:.2f}")
        print("-" * 50)

if __name__ == "__main__":
    check_trend()
