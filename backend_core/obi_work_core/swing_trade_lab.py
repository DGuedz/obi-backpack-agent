import time
import sys
import os
import uuid

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

class SwingTradeLab:
    """
    OBI WORK - SWING TRADE LAB
    Modality: Swing Trader
    Timeframe: 4h
    Strategy: MACD (12, 26, 9) Trend Following
    """
    
    def __init__(self, symbol="SOL_USDC"):
        self.client = BackpackClient()
        self.symbol = symbol
        self.session_id = str(uuid.uuid4())[:8]
        
    def calculate_ema(self, data: list, period: int) -> list:
        if len(data) < period:
            return []
        k = 2 / (period + 1)
        ema = []
        sma = sum(data[:period]) / period
        ema.append(sma)
        for price in data[period:]:
            new_ema = (price * k) + (ema[-1] * (1 - k))
            ema.append(new_ema)
        return ema

    def calculate_macd(self, data: list) -> dict:
        # Standard MACD (12, 26, 9)
        if len(data) < 26:
            return {}
            
        ema12 = self.calculate_ema(data, 12)
        ema26 = self.calculate_ema(data, 26)
        
        # Align lengths (EMA26 starts later)
        # We need the last N values where both exist
        # EMA12 will have (len - 12 + 1) values
        # EMA26 will have (len - 26 + 1) values
        
        # To subtract, we match the end of the arrays
        min_len = min(len(ema12), len(ema26))
        
        macd_line = []
        # Take last min_len from both
        e12_slice = ema12[-min_len:]
        e26_slice = ema26[-min_len:]
        
        for i in range(min_len):
            macd_line.append(e12_slice[i] - e26_slice[i])
            
        # Signal Line (9 EMA of MACD Line)
        signal_line = self.calculate_ema(macd_line, 9)
        
        if not signal_line:
            return {}
            
        # Histogram
        # Align again
        min_len_hist = min(len(macd_line), len(signal_line))
        histogram = []
        
        m_slice = macd_line[-min_len_hist:]
        s_slice = signal_line[-min_len_hist:]
        
        for i in range(min_len_hist):
            histogram.append(m_slice[i] - s_slice[i])
            
        return {
            "macd": m_slice,
            "signal": s_slice,
            "hist": histogram
        }

    def run_analysis(self):
        print(f"\n🌊 SWING TRADE LAB (Session: {self.session_id})")
        print(f"Asset: {self.symbol} | Timeframe: 4h")
        print("=" * 50)
        
        # 1. Fetch Candles
        print("1. Fetching Market Data (4h)...")
        # Need enough data for EMA26 + Signal9
        candles = self.client.get_candles(self.symbol, "4h", limit=100)
        
        if not candles:
            print("❌ Failed to fetch candles.")
            return

        try:
            closes = [float(c['close']) for c in candles]
            current_price = closes[-1]
            print(f"   Current Price: ${current_price:.2f}")
        except Exception as e:
            print(f"❌ Error parsing candles: {e}")
            return
            
        # 2. Calculate MACD
        print("2. Calculating Indicators (MACD 12/26/9)...")
        indicators = self.calculate_macd(closes)
        
        if not indicators or not indicators.get("macd"):
            print("   Not enough data for MACD.")
            return
            
        macd_val = indicators["macd"][-1]
        signal_val = indicators["signal"][-1]
        hist_val = indicators["hist"][-1]
        prev_hist = indicators["hist"][-2]
        
        print(f"   MACD Line:   {macd_val:.4f}")
        print(f"   Signal Line: {signal_val:.4f}")
        print(f"   Histogram:   {hist_val:.4f}")
        
        # 3. Signal Generation
        print("3. Generating Signal...")
        signal = "NEUTRAL"
        
        if macd_val > signal_val:
            signal = "BULLISH (Up Trend)"
            if prev_hist < 0 and hist_val > 0:
                signal = "BUY SIGNAL (Crossover)"
        elif macd_val < signal_val:
            signal = "BEARISH (Down Trend)"
            if prev_hist > 0 and hist_val < 0:
                signal = "SELL SIGNAL (Crossover)"
                
        print(f"   Signal: {signal}")
        
        # 4. Swing Setup
        if "BULLISH" in signal or "BUY" in signal:
            sl = current_price * 0.95 # 5% SL (Wider for Swing)
            tp = current_price * 1.10 # 10% TP
            print(f"\n🎯 SWING SETUP (Long):")
            print(f"   Entry: ${current_price:.2f}")
            print(f"   SL:    ${sl:.2f} (-5%)")
            print(f"   TP:    ${tp:.2f} (+10%)")
            print(f"   R/R:   1:2")
        elif "BEARISH" in signal or "SELL" in signal:
            sl = current_price * 1.05 # 5% SL
            tp = current_price * 0.90 # 10% TP
            print(f"\n🎯 SWING SETUP (Short):")
            print(f"   Entry: ${current_price:.2f}")
            print(f"   SL:    ${sl:.2f} (-5%)")
            print(f"   TP:    ${tp:.2f} (+10%)")
            print(f"   R/R:   1:2")
            
        print("\n✅ Swing Trade Analysis Complete.")

if __name__ == "__main__":
    lab = SwingTradeLab(symbol="SOL_USDC")
    lab.run_analysis()
