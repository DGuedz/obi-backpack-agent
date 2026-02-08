import time
import sys
import os
import uuid

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

class PositionLab:
    """
    OBI WORK - POSITION LAB (HODL)
    Modality: Position Trader
    Timeframe: 1d (Daily)
    Strategy: Golden Cross (SMA 50/200) + Trend Filter
    """
    
    def __init__(self, symbol="SOL_USDC"):
        self.client = BackpackClient()
        self.symbol = symbol
        self.session_id = str(uuid.uuid4())[:8]
        
    def calculate_sma(self, data: list, period: int) -> list:
        if len(data) < period:
            return []
        
        sma = []
        # Calculate moving average
        for i in range(len(data) - period + 1):
            window = data[i:i+period]
            avg = sum(window) / period
            sma.append(avg)
            
        # The result 'sma' has length len(data) - period + 1
        # It aligns with the END of the data window.
        # So sma[-1] corresponds to data[-1]
        return sma

    def run_analysis(self):
        print(f"\n🏰 POSITION LAB (Session: {self.session_id})")
        print(f"Asset: {self.symbol} | Timeframe: 1d")
        print("=" * 50)
        
        # 1. Fetch Candles
        print("1. Fetching Market Data (Daily)...")
        # Need 200 days for SMA200
        candles = self.client.get_candles(self.symbol, "1d", limit=300)
        
        if not candles or len(candles) < 200:
            print(f"❌ Failed to fetch enough candles. Got {len(candles) if candles else 0}.")
            return

        try:
            closes = [float(c['close']) for c in candles]
            current_price = closes[-1]
            print(f"   Current Price: ${current_price:.2f}")
        except Exception as e:
            print(f"❌ Error parsing candles: {e}")
            return
            
        # 2. Calculate Indicators
        print("2. Calculating Indicators (SMA 50/200)...")
        sma50 = self.calculate_sma(closes, 50)
        sma200 = self.calculate_sma(closes, 200)
        
        if not sma50 or not sma200:
            print("   Not enough data for SMA calculation.")
            return
            
        curr_sma50 = sma50[-1]
        curr_sma200 = sma200[-1]
        
        print(f"   SMA 50:  ${curr_sma50:.2f}")
        print(f"   SMA 200: ${curr_sma200:.2f}")
        
        # 3. Signal Generation
        print("3. Generating Signal...")
        trend = "NEUTRAL"
        
        if curr_sma50 > curr_sma200:
            trend = "BULLISH (Golden Cross)"
            # Check proximity for entry?
        elif curr_sma50 < curr_sma200:
            trend = "BEARISH (Death Cross)"
            
        print(f"   Trend: {trend}")
        
        # Distance from SMA 200 (Mean Reversion / Value Zone)
        dist_pct = ((current_price - curr_sma200) / curr_sma200) * 100
        print(f"   Distance from SMA 200: {dist_pct:.2f}%")
        
        # 4. Position Setup
        if "BULLISH" in trend:
            if dist_pct < 20: # If price is not too extended (<20% above SMA200)
                print("\n💎 HODL SETUP (Buy):")
                print("   Action: Accumulate / Hold")
                print("   Reason: Golden Cross + Healthy Trend")
            else:
                print("\n⚠️ HODL UPDATE:")
                print("   Action: Hold (Overextended)")
                print("   Reason: Price > 20% above SMA200. Wait for pullback.")
        elif "BEARISH" in trend:
            print("\n🛡️ HODL SETUP (Defensive):")
            print("   Action: Cash / Stablecoins")
            print("   Reason: Death Cross (Bear Market)")
            
        print("\n✅ Position Analysis Complete.")

if __name__ == "__main__":
    lab = PositionLab(symbol="SOL_USDC")
    lab.run_analysis()
