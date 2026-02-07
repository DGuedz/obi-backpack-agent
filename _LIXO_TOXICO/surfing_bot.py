
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

class SurfingBot:
    def __init__(self):
        self.symbol = "IP_USDC_PERP"
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        
        # Config
        self.quantity_usd = 100
        self.leverage = 10
        self.trailing_stop_pct = 0.015 # 1.5% Trailing
        self.entry_price = 0
        self.highest_price = 0
        self.position = None # 'Long', 'Short', None

    def get_market_metrics(self):
        # 1. Fetch 5m Candles (Better for surfing than 1m)
        klines = self.data.get_klines(self.symbol, interval="5m", limit=50)
        if not klines: return None

        df = pd.DataFrame(klines)
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            df[col] = df[col].astype(float)
            
        # 2. Calc EMA 9 (The Surfing Board)
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        
        # 3. Calc RSI (Momentum Fuel)
        rsi = self.indicators.calculate_rsi(df, window=14)
        
        last = df.iloc[-1]
        metrics = {
            'price': last['close'],
            'ema9': last['ema9'],
            'rsi': rsi.iloc[-1],
            'trend': 'UP' if last['close'] > last['ema9'] else 'DOWN'
        }
        return metrics

    def run_cycle(self):
        print(f" SURFING BOT: Scanning {self.symbol}...")
        
        metrics = self.get_market_metrics()
        if not metrics:
            print(" No Data.")
            return

        price = metrics['price']
        ema9 = metrics['ema9']
        rsi = metrics['rsi']
        trend = metrics['trend']
        
        print(f"    Price: {price:.4f} | EMA9: {ema9:.4f} | RSI: {rsi:.1f} | Trend: {trend}")
        
        # 1. Check Active Position (API)
        positions = self.data.get_positions()
        pos = next((p for p in positions if p['symbol'] == self.symbol), None)
        
        if pos:
            self.manage_position(pos, price)
        else:
            self.find_entry(metrics)

    def find_entry(self, metrics):
        # Entry Logic: Breakout of EMA9 with Momentum
        # If Trend UP and RSI > 50 and RSI < 70 -> Long
        # If Trend DOWN and RSI < 50 and RSI > 30 -> Short
        
        price = metrics['price']
        ema9 = metrics['ema9']
        rsi = metrics['rsi']
        
        signal = None
        
        # SHORT SURF (Following the dump trend)
        if price < ema9 and rsi < 50:
             # Check if we are not too oversold
             if rsi > 25:
                 signal = "Short"
                 print("    SIGNAL: SURF DOWN (Price < EMA9 + RSI Bearish)")
        
        # LONG SURF (Reversal)
        elif price > ema9 and rsi > 55:
             signal = "Long"
             print("    SIGNAL: SURF UP (Price > EMA9 + RSI Bullish)")
             
        if signal:
            self.execute_entry(signal, price)

    def execute_entry(self, side, price):
        print(f" PADDLING IN... {side} Entry!")
        qty = self.quantity_usd / price * self.leverage
        qty = round(qty, 1)
        
        order_side = "Bid" if side == "Long" else "Ask"
        
        # Market Entry for Surfing (Don't miss the wave)
        # Or Aggressive Limit
        res = self.trade.execute_order(
            symbol=self.symbol,
            side=order_side,
            price=None,
            quantity=str(qty),
            order_type="Market"
        )
        
        if res and 'id' in res:
            print(f" CAUGHT THE WAVE: {res['id']}")
            self.position = side
            self.entry_price = price
            self.highest_price = price if side == "Long" else price # Lowest for short
            
            # Place Initial Stop Loss (Hard)
            self.update_trailing_stop(side, price, qty, initial=True)

    def manage_position(self, pos, current_price):
        side = pos['side'] # Long/Short
        qty = float(pos['quantity'])
        entry = float(pos['entryPrice'])
        
        print(f"    RIDING WAVE: {side} (PnL: {pos['pnlUnrealized']})")
        
        # Dynamic Trailing Stop Logic
        # Update trailing trigger based on price movement
        
        # For this demo, we assume we update the SL order on the exchange
        # But updating every cycle might hit rate limits.
        # Better: Check if price hit our internal trailing mark, then close.
        
        # Calculate Trailing Mark
        if side == "Long":
             if current_price > self.highest_price:
                 self.highest_price = current_price
             
             stop_price = self.highest_price * (1 - self.trailing_stop_pct)
             
             if current_price < stop_price:
                 print(f"    TRAILING STOP HIT! Closing Long at {current_price}")
                 self.trade.close_position(self.symbol, qty)
                 
        else: # Short
             if self.highest_price == 0: self.highest_price = entry # Init
             if current_price < self.highest_price: # Lower is better for short
                 self.highest_price = current_price
                 
             stop_price = self.highest_price * (1 + self.trailing_stop_pct)
             
             if current_price > stop_price:
                 print(f"    TRAILING STOP HIT! Closing Short at {current_price}")
                 self.trade.close_position(self.symbol, -qty)

    def update_trailing_stop(self, side, price, qty, initial=False):
        # Place Hard Stop initially
        sl_price = price * (1 - 0.02) if side == "Long" else price * (1 + 0.02)
        sl_side = "Ask" if side == "Long" else "Bid"
        
        # Just fire and forget for safety (2% hard stop)
        if initial:
            # Using Trigger Limit simulation
            trigger = sl_price
            limit = sl_price * 0.95 if side == "Long" else sl_price * 1.05
            
            self.trade.execute_order(
                self.symbol, sl_side, f"{limit:.4f}", str(qty), 
                "StopLimit", trigger_price=f"{trigger:.4f}", reduce_only=True
            )
            print("   ️ Safety Leash Attached (Hard SL 2%)")

if __name__ == "__main__":
    bot = SurfingBot()
    while True:
        try:
            bot.run_cycle()
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
