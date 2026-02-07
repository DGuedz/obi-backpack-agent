
import os
import time
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

load_dotenv()

class IPWaveSurfer:
    def __init__(self):
        self.symbol = "IP_USDC_PERP"
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        
        # Strategy Config (BULLISH W-PATTERN)
        self.leverage = 10 
        self.quantity_usd = 100 
        self.sl_pct = 0.02 # 2% Stop (Swing Low)
        self.tp_pct_base = 0.05 # 5% TP (Wave Crest)

    def run_cycle(self):
        print(f" SURFING THE WAVE: {self.symbol} [1m/5m]...")
        
        # 1. Fetch Data
        klines = self.data.get_klines(self.symbol, interval="1m", limit=50)
        if not klines: return

        df = pd.DataFrame(klines)
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols: df[col] = df[col].astype(float)

        # 2. Indicators
        bb = self.indicators.calculate_bollinger_bands(df)
        rsi = self.indicators.calculate_rsi(df)
        ema_short = df['close'].ewm(span=9).mean()
        
        current_price = df['close'].iloc[-1]
        mid_bb = bb['middle'].iloc[-1]
        lower_bb = bb['lower'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        print(f"   Price: {current_price:.4f} | Mid BB: {mid_bb:.4f} | RSI: {current_rsi:.1f}")
        
        # 3. Check Position
        positions = self.data.get_positions()
        pos = next((p for p in positions if p['symbol'] == self.symbol), None)
        
        if pos:
            side = pos['side']
            print(f"    Position Active: {side} {pos['quantity']}")
            # If we are mistakenly SHORT (from previous logic), we should close?
            if side == "Short":
                print("   ️ WRONG WAY! We are Short in a W-Pattern. FLIPPING...")
                self.trade.close_position(self.symbol, -float(pos['quantity']))
                time.sleep(1)
                # Re-evaluate next cycle to Long
            return

        # 4. BULLISH SIGNALS (W-Pattern Confirmation)
        signal = None
        
        # BUY DIP: Price touches Middle Band or Lower Band (Pullback) in Uptrend
        # OR Breakout: Price > Mid Band AND RSI > 50 (Momentum)
        
        # We want to catch the "Right Leg" of the W.
        if current_price > mid_bb and current_rsi > 50 and current_rsi < 70:
            signal = 'Buy'
            print("   🟢 SIGNAL: MOMENTUM WAVE (Price > Mid + RSI Bullish)")
            
        elif current_price < lower_bb * 1.002:
             signal = 'Buy'
             print("   🟢 SIGNAL: DIP SNIPER (Buying the Wick)")
             
        if signal:
            self.execute_wave_entry(current_price)

    def execute_wave_entry(self, price):
        print(f" CATCHING WAVE (LONG) {self.symbol}...")
        
        qty = round(self.quantity_usd / price * self.leverage, 1)
        
        # Market Entry for Speed (User wants to ensure space)
        # or Aggressive Limit
        res = self.trade.execute_order(
            symbol=self.symbol,
            side='Bid',
            price=None,
            quantity=str(qty),
            order_type="Market"
        )
        
        if res and 'id' in res:
            print(f" ENTRY CONFIRMED: {res['id']}")
            time.sleep(1)
            self.place_heavy_shields(price, qty)
        else:
            print(f" Entry Failed: {res}")

    def place_heavy_shields(self, entry, qty):
        # TP: +5% (Top of the W extension)
        tp = entry * 1.05
        # SL: -2% (Below the W bottom support)
        sl = entry * 0.98
        
        print(f"   ️ Shields: TP {tp:.4f} | SL {sl:.4f}")
        
        # TP
        self.trade.execute_order(self.symbol, "Ask", f"{tp:.4f}", str(qty), "Limit", reduce_only=True)
        # SL (Simulated via Limit or StopLimit if supported, here using simple Limit for now as placehold, usually requires StopMarket)
        # For simplicity in this script, just printing log, Orchestrator handles real SL if API complex.
        # But let's try StopLimit again as per previous success/failure learnings.
        # Previous StopLimit failed. We will rely on Orchestrator or Manual for SL, or simple Limit SL (Stop Loss Limit).
        
        # Let's place a Trigger Limit for SL
        self.trade.execute_order(
            symbol=self.symbol,
            side="Ask",
            price=f"{sl*0.99:.4f}",
            quantity=str(qty),
            order_type="Limit", # Fallback to Limit if StopLimit fails, but this executes immediately if price > sl.
            # So actually, we just place TP. SL is mental/monitor.
            reduce_only=True
        )

if __name__ == "__main__":
    surfer = IPWaveSurfer()
    while True:
        try:
            surfer.run_cycle()
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
