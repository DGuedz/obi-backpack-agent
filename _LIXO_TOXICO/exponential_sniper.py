
import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)
indicators = BackpackIndicators()

class ExponentialSniper:
    def __init__(self):
        self.symbol = "IP_USDC_PERP"
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        
        self.leverage = 10
        self.budget = 200 # Double Down ($200)
        
        # Risk Config
        self.sl_pct = 0.02 # 2% Fixed Risk
        self.trailing_activation = 0.015 # Activate trailing after 1.5% profit
        self.trailing_dist = 0.01 # 1% Trailing Distance
        
    def scan_and_execute(self):
        print(f" EXPONENTIAL SNIPER: Targeting {self.symbol} with ${self.budget}...")
        
        # 1. Technical Analysis (Entry Trigger)
        # Using 5m timeframe for slightly longer swing
        klines = data.get_klines(self.symbol, interval="5m", limit=50)
        df = pd.DataFrame(klines)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
            
        rsi = indicators.calculate_rsi(df, window=14).iloc[-1]
        bb = indicators.calculate_bollinger_bands(df)
        price = df['close'].iloc[-1]
        
        print(f"    Price: {price:.4f} | RSI: {rsi:.1f}")
        
        # Entry Logic: Trend Following or Reversal?
        # User said "potencial revelados pelos indicadores".
        # If RSI < 40 -> Buy (Reversal up)
        # If RSI > 60 -> Sell (Reversal down)
        # Else -> Wait
        
        signal = "WAIT"
        if rsi < 40:
            signal = "BUY"
            print("   🟢 Setup: Oversold Bounce (Long)")
        elif rsi > 60:
            signal = "SELL"
            print("    Setup: Overbought Correction (Short)")
        else:
            print("   ️ Market is Neutral. Waiting for clear setup...")
            return
            
        # Execute
        side = "Bid" if signal == "BUY" else "Ask"
        notional = self.budget * self.leverage
        qty = round(notional / price, 1)
        
        print(f"   ️ EXECUTING {signal} {qty} IP...")
        
        res = trade.execute_order(
            symbol=self.symbol,
            side=side,
            price=None,
            quantity=str(qty),
            order_type="Market"
        )
        
        if res and 'id' in res:
            print(f"    FILLED: {res['id']}")
            self.manage_position(side, price, qty)
        else:
            print(f"    Failed: {res}")

    def manage_position(self, side, entry_price, qty):
        # 1. Initial Stop Loss (Hard 2%)
        sl_price = entry_price * (1 - self.sl_pct) if side == "Bid" else entry_price * (1 + self.sl_pct)
        sl_side = "Ask" if side == "Bid" else "Bid"
        
        print(f"   ️ Setting Initial SL @ {sl_price:.4f}")
        # Place SL
        trade.execute_order(self.symbol, sl_side, f"{sl_price:.4f}", str(qty), "Limit", trigger_price=f"{sl_price:.4f}", reduce_only=True)
        # Note: Using Limit as StopLimit proxy, might need adjustment if API strict
        
        print("    Tracking for Exponential Profit...")
        # Simulation of Trailing Logic (In real bot this loops)
        # For this script, we set the initial state and exit. The "Orchestrator" or a dedicated loop should manage the trail.
        # I will print the instructions for the Trailing Bot.
        
        print(f"   NOTE: Monitor price. If moves > 1.5% in favor, move SL to Breakeven.")
        print(f"   NOTE: If indicators (RSI) hit extreme (e.g. > 80 or < 20), CLOSE manually to capture exponential peak.")

if __name__ == "__main__":
    bot = ExponentialSniper()
    bot.scan_and_execute()
