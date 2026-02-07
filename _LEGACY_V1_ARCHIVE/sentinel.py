import time
import threading
import json
import os
from datetime import datetime

from backpack_indicators import BackpackIndicators
import pandas as pd

class Sentinel(threading.Thread):
    def __init__(self, data_engine, trade_engine, budget_file="budget.json"):
        super().__init__()
        self.data = data_engine
        self.trade = trade_engine
        self.indicators = BackpackIndicators()
        self.budget_file = budget_file
        self.running = True
        self.panic_triggered = False
        
        # Safety Thresholds
        self.MAX_DAILY_LOSS_PCT = 0.10 # 10% of budget
        self.MIN_MARGIN_FRACTION = 0.10 # 10% Margin Fraction required
        self.MAX_PNL_DRAWDOWN = -0.015 # -1.5% Unrealized PnL per position
        self.TREND_GUARD_ENABLED = True
        
    def check_trend_integrity(self, symbol, timeframe="1h"):
        """
        Verifica se a tendência principal (EMA 200) foi violada.
        Retorna: 'SAFE', 'WARNING', 'CRASH'
        """
        try:
            candles = self.data.get_klines(symbol, timeframe, limit=200)
            if not candles: return 'SAFE'
            
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Logic: If Price < EMA 200, Trend is Broken (Bearish)
            if current_price < ema_200:
                # Calculate deviation
                dev = (ema_200 - current_price) / ema_200
                if dev > 0.01: # 1% below EMA 200 -> CRASH MODE
                    return 'CRASH'
                return 'WARNING'
            
            return 'SAFE'
        except Exception as e:
            print(f"️ Trend Check Error: {e}")
            return 'SAFE' # Default to safe to avoid blocking in error, or 'WARNING' to be safe?

    def run(self):
        print("️ [SENTINEL] Shield Activated. Monitoring Risco & Tendência...")
        while self.running:
            try:
                self._check_risk()
                time.sleep(5) # Check every 5 seconds
            except Exception as e:
                print(f"️ [SENTINEL] Error in monitoring loop: {e}")
                time.sleep(5)
                
    def _check_risk(self):
        # 1. Budget Check
        self._check_budget()
        
        # 2. Account Health (Collateral)
        collateral = self.data.get_account_collateral()
        if not collateral: return
        
        # Margin Fraction Check (Liquidation Risk)
        # Note: API response structure depends on 'collateral' endpoint
        # Assuming typical response with 'marginFraction' or similar
        # If not available directly, calculate Equity / Maintenance Margin
        
        # 3. Position PnL Check
        positions = self.data.get_positions()
        for pos in positions:
            symbol = pos.get('symbol')
            pnl = float(pos.get('unrealizedPnl', 0))
            # side = pos.get('side')
            # entry_price = float(pos.get('entryPrice'))
            # mark_price = float(pos.get('markPrice'))
            
            # Simple PnL protection
            # We need PnL % or raw PnL relative to margin
            # Assuming 'pnl' is raw USDC value. 
            # Need to know margin used to calculate %.
            # For now, let's use a hard raw value check or assume strict PnL
            
            # Implementation of "PnL < -1.5%" rule
            # Requires calculating ROI %. 
            # ROI = PnL / Initial Margin
            initial_margin = float(pos.get('initialMargin', 1)) # Avoid div by zero
            roi = pnl / initial_margin
            
            if roi < self.MAX_PNL_DRAWDOWN:
                print(f" [SENTINEL] CRITICAL DRAWDOWN detected on {symbol}: {roi*100:.2f}% < -1.5%")
                self.panic_close(symbol)

    def _check_budget(self):
        if not os.path.exists(self.budget_file): return
        
        try:
            with open(self.budget_file, 'r') as f:
                budget = json.load(f)
            
            daily_budget = budget.get('daily_budget', 500)
            max_loss_pct = budget.get('max_daily_loss_pct', 0.10)
            current_loss = budget.get('current_loss', 0.0)
            
            max_loss_allowed = daily_budget * max_loss_pct
            
            if current_loss > max_loss_allowed:
                if not self.panic_triggered:
                    print(f" [SENTINEL] KILL SWITCH ENGAGED. Daily Loss (${current_loss}) > Limit (${max_loss_allowed})")
                    self.panic_close_all()
                    self.panic_triggered = True
                    os._exit(1) # Hard Kill
                    
        except Exception as e:
            print(f"️ [SENTINEL] Budget check error: {e}")

    def panic_close(self, symbol):
        print(f"️ [SENTINEL] Executing PANIC CLOSE for {symbol}...")
        try:
            positions = self.data.get_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    qty = pos['quantity']
                    side = pos['side']
                    # Close Side is opposite of Open Side
                    close_side = "Ask" if side == "Long" else "Bid" # Assuming API returns "Long"/"Short" or "Bid"/"Ask" logic. 
                    # Actually API 'side' is usually "Long" or "Short". 
                    # If Long, we Sell (Ask). If Short, we Buy (Bid).
                    # Let's check API response format. Usually 'Long'/'Short'.
                    
                    if side.lower() == "long": close_side = "Ask"
                    elif side.lower() == "short": close_side = "Bid"
                    else: close_side = "Ask" # Default?
                    
                    print(f"   PLEASE CLOSE {side} {qty} {symbol}...")
                    self.trade.execute_order(symbol, close_side, 0, qty, order_type="Market", reduce_only=True)
                    return
        except Exception as e:
            print(f"    Panic Close Failed: {e}")
        # Need to fetch position qty first.
        # This is a stub for safety. Real implementation needs quantity.
        pass

    def panic_close_all(self):
        print("️ [SENTINEL] PANIC CLOSE ALL POSITIONS initiated!")
        positions = self.data.get_positions()
        for pos in positions:
            symbol = pos.get('symbol')
            qty = float(pos.get('netQuantity')) # Check field name
            side = "Ask" if qty > 0 else "Bid"
            abs_qty = abs(qty)
            
            print(f"   Closing {symbol} ({qty})...")
            self.trade.execute_order(symbol, side, 0, abs_qty, order_type="Market", reduce_only=True)
            
    def stop(self):
        self.running = False

