import time
import sys
import os
import uuid

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

class DayTradeLab:
    """
    OBI WORK - DAY TRADE LAB
    Modality: Day Trader
    Timeframe: 15m / 1h
    Strategy: EMA Crossover (9/21) + Trend Following
    """
    
    def __init__(self, symbol="SOL_USDC"):
        self.client = BackpackClient()
        self.symbol = symbol
        self.session_id = str(uuid.uuid4())[:8]
        
    def calculate_ema(self, data: list, period: int) -> list:
        # Simple EMA calculation
        if len(data) < period:
            return []
            
        k = 2 / (period + 1)
        ema = []
        
        # Start with SMA
        sma = sum(data[:period]) / period
        ema.append(sma)
        
        # Calculate EMA
        for price in data[period:]:
            new_ema = (price * k) + (ema[-1] * (1 - k))
            ema.append(new_ema)
            
        return ema

    def run_analysis(self):
        print(f"\n☀️ DAY TRADE LAB (Session: {self.session_id})")
        print(f"Asset: {self.symbol} | Timeframe: 15m")
        print("=" * 50)
        
        # 1. Fetch Candles
        print("1. Fetching Market Data (15m)...")
        candles = self.client.get_candles(self.symbol, "15m", limit=50)
        
        if not candles:
            print("❌ Failed to fetch candles.")
            return

        # Backpack Candle format: {"open": "...", "close": "...", ...} ?? 
        # Actually usually list of dicts or list of lists.
        # Let's inspect format based on previous usage. 
        # Previous usage in agent_loop didn't parse yet?
        # Standard Backpack API returns list of dicts usually.
        # Let's assume list of dicts with 'close'.
        
        try:
            closes = [float(c['close']) for c in candles]
            # Reverse? Usually API returns Newest Last or Oldest Last?
            # Backpack API usually returns Oldest First (Ascending Time).
            # So closes[-1] is the most recent.
        except Exception as e:
            print(f"❌ Error parsing candles: {e}")
            print(f"Sample: {candles[0] if candles else 'Empty'}")
            return
            
        current_price = closes[-1]
        print(f"   Current Price: ${current_price:.2f}")
        
        # 2. Technical Analysis (EMA)
        print("2. Calculating Indicators (EMA 9/21)...")
        ema9 = self.calculate_ema(closes, 9)
        ema21 = self.calculate_ema(closes, 21)
        
        if not ema9 or not ema21:
            print("   Not enough data for EMA.")
            return
            
        curr_ema9 = ema9[-1]
        curr_ema21 = ema21[-1]
        
        print(f"   EMA 9:  ${curr_ema9:.2f}")
        print(f"   EMA 21: ${curr_ema21:.2f}")
        
        # 3. Signal Generation
        print("3. Generating Signal...")
        signal = "NEUTRAL"
        
        # Crossover Logic
        if curr_ema9 > curr_ema21:
            signal = "BULLISH (Buy Trend)"
            # Check if crossed recently?
            prev_ema9 = ema9[-2]
            prev_ema21 = ema21[-2]
            if prev_ema9 <= prev_ema21:
                signal = "GOLDEN CROSS (Strong Buy)"
        elif curr_ema9 < curr_ema21:
            signal = "BEARISH (Sell Trend)"
            prev_ema9 = ema9[-2]
            prev_ema21 = ema21[-2]
            if prev_ema9 >= prev_ema21:
                signal = "DEATH CROSS (Strong Sell)"
                
        print(f"   Signal: {signal}")
        
        # 4. Day Trade Setup (Theoretical)
        if "BULLISH" in signal:
            sl = current_price * 0.99 # 1% SL
            tp = current_price * 1.02 # 2% TP
            print(f"\n🎯 SETUP (Long):")
            print(f"   Entry: ${current_price:.2f}")
            print(f"   SL:    ${sl:.2f} (-1%)")
            print(f"   TP:    ${tp:.2f} (+2%)")
            print(f"   R/R:   1:2")
        elif "BEARISH" in signal:
            sl = current_price * 1.01 # 1% SL
            tp = current_price * 0.98 # 2% TP
            print(f"\n🎯 SETUP (Short):")
            print(f"   Entry: ${current_price:.2f}")
            print(f"   SL:    ${sl:.2f} (-1%)")
            print(f"   TP:    ${tp:.2f} (+2%)")
            print(f"   R/R:   1:2")
            
        print("\n✅ Day Trade Analysis Complete.")

if __name__ == "__main__":
    lab = DayTradeLab(symbol="SOL_USDC")
    lab.run_analysis()
