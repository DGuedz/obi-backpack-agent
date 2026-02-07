
import os
import time
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# Load environment variables
load_dotenv()

class IPScalper:
    def __init__(self):
        self.symbol = "IP_USDC_PERP"
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        
        # Strategy Config
        self.leverage = 5 # Adjusted to 5x as per user "Option B" in intelligence report? 
        # Wait, user said "Option B ... leverage 5" in the report text, but "vamos operar com 100 dolares a 10x" in the input.
        # "10x" in input overrides previous "5x" in report.
        self.leverage = 10 
        self.quantity_usd = 100 # "100 dolares"
        
        # Risk Management
        self.sl_pct = 0.01 # 1% Stop
        self.tp_pct_base = 0.015 # 1.5% TP (Base)

    def run_cycle(self):
        print(f" Scanning {self.symbol} [1m]...")
        
        # 1. Fetch Data
        klines = self.data.get_klines(self.symbol, interval="1m", limit=50)
        if not klines:
            print(" No Data.")
            return

        df = pd.DataFrame(klines)
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            df[col] = df[col].astype(float)

        # 2. Indicators
        bb = self.indicators.calculate_bollinger_bands(df, window=20, window_dev=2.0)
        rsi = self.indicators.calculate_rsi(df, window=14)
        
        current_price = df['close'].iloc[-1]
        lower = bb['lower'].iloc[-1]
        upper = bb['upper'].iloc[-1]
        mid = bb['middle'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        
        print(f"   Price: {current_price:.4f} | BB: {lower:.4f} - {upper:.4f} | RSI: {current_rsi:.1f}")
        
        # 3. Check Active Position
        positions = self.data.get_positions()
        active_pos = next((p for p in positions if p['symbol'] == self.symbol), None)
        
        if active_pos:
            print(f"   ️ Position Active: {active_pos['side']} {active_pos['quantity']}")
            return

        # 4. Signal Logic (SHORT-TERM BEARISH BIAS as per user request)
        signal = None
        
        # SHORT SIGNAL (Aggressive):
        # If Price is in Upper Half of BB (Above Mid) AND RSI > 55 (Weak Overbought)
        # OR Price just touched Upper Band recently
        if current_price > mid and current_rsi > 55:
             signal = 'Sell'
             print("    SIGNAL: BEARISH SCALP (Price > Mid + RSI > 55)")
             
        # LONG SIGNAL (Defensive/Reversal only):
        # Only if Deep Oversold (RSI < 30)
        elif current_price < lower and current_rsi < 30:
             signal = 'Buy'
             print("   🟢 SIGNAL: DEEP OVERSOLD REVERSAL (Price < Lower + RSI < 30)")

        if signal:
            self.execute_trade(signal, current_price, mid)

    def execute_trade(self, side, price, tp_target_price):
        print(f" EXECUTING {side} {self.symbol}...")
        
        # Calc Quantity
        qty = self.quantity_usd / price * self.leverage
        qty = round(qty, 1) # Adjust precision as needed
        
        # 1. Entry Order (Maker - Post Only)
        # Use a slightly aggressive limit price to ensure fill if it's moving fast, but postOnly protects us.
        # If Buying, Limit = Price * 0.9995? No, if we want to fill, we should be close.
        # User said "Maker strategy".
        limit_price = price 
        
        res = self.trade.execute_order(
            symbol=self.symbol,
            side='Bid' if side == 'Buy' else 'Ask',
            price=f"{limit_price:.4f}",
            quantity=str(qty),
            order_type="Limit",
            post_only=True
        )
        
        if not res or 'id' not in res:
            print(" Entry Order Failed (Likely Taker Rejection). Waiting for next cycle.")
            return

        print(f" Entry Order Placed: {res['id']}")
        
        # 2. GUARDIAN PROTOCOL: Aggressive Protection Placement
        # We poll faster (0.5s) to detect fill and place protection IMMEDIATELY.
        print("️ GUARDIAN: Watching for fill to deploy shields...")
        
        max_retries = 20 # 10 seconds (0.5s * 20)
        filled = False
        
        for _ in range(max_retries):
            time.sleep(0.5)
            positions = self.data.get_positions()
            pos = next((p for p in positions if p['symbol'] == self.symbol), None)
            
            if pos:
                print(" GUARDIAN: Fill Confirmed! Deploying TP/SL NOW...")
                success = self.place_protection(side, price, qty, tp_target_price)
                if not success:
                    print(" GUARDIAN ALERT: Protection Failed! CLOSING POSITION IMMEDIATELY.")
                    self.trade.close_position(self.symbol, float(pos['quantity']) if pos['side'] == 'Long' else -float(pos['quantity']))
                return
        
        print("️ Order not filled in 10s. Cancelling to reset...")
        self.trade.cancel_open_orders(self.symbol)

    def place_protection(self, side, entry_price, qty, tp_target):
        try:
            # TP
            tp_price = entry_price * (1 + self.tp_pct_base) if side == 'Buy' else entry_price * (1 - self.tp_pct_base)
            tp_side = 'Ask' if side == 'Buy' else 'Bid'
            
            # SL
            sl_price = entry_price * (1 - self.sl_pct) if side == 'Buy' else entry_price * (1 + self.sl_pct)
            sl_side = 'Ask' if side == 'Buy' else 'Bid'
            
            # Place TP (Limit ReduceOnly)
            print(f"   ️ Setting TP at {tp_price:.4f}...")
            res_tp = self.trade.execute_order(
                symbol=self.symbol,
                side=tp_side,
                price=f"{tp_price:.4f}",
                quantity=str(qty),
                order_type="Limit",
                reduce_only=True
            )
            
            # Place SL (Stop Limit)
            # Trigger = sl_price
            # Limit = sl_price * 0.9 (Buy) or 1.1 (Sell) to ensure fill like Market
            sl_limit_price = sl_price * 0.95 if side == 'Buy' else sl_price * 1.05
            
            print(f"   ️ Setting SL at {sl_price:.4f}...")
            res_sl = self.trade.execute_order(
                symbol=self.symbol,
                side=sl_side,
                price=f"{sl_limit_price:.4f}",
                quantity=str(qty),
                order_type="StopLimit", # Assuming API supports this map
                trigger_price=f"{sl_price:.4f}",
                reduce_only=True
            )
            
            if res_tp and res_sl:
                print("    SHIELDS UP: TP and SL Active.")
                return True
            else:
                print(f"    Partial Shield Failure: TP={res_tp}, SL={res_sl}")
                return False
                
        except Exception as e:
            print(f"    EXCEPTION in Protection: {e}")
            return False

if __name__ == "__main__":
    bot = IPScalper()
    while True:
        try:
            bot.run_cycle()
            time.sleep(10) # 1m candles, check every 10s
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
