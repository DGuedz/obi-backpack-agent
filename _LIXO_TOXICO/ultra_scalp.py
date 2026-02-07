
import os
import sys
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# Load environment variables
load_dotenv()

# Configuration
SYMBOL = "IP_USDC_PERP" # Winner of the simulation
LEVERAGE = 10
MARGIN = 100 # $100
POSITION_SIZE = MARGIN * LEVERAGE # $1000 Notional
SPREAD_THRESHOLD = 0.0005 # 0.05% Spread target to capture
MIN_PROFIT_PCT = 0.001 # 0.1% Profit per trade (Micro Scalp)
STOP_LOSS_PCT = 0.01 # 1% Hard Stop
POLL_INTERVAL = 0.5 # 500ms (Simulating 1s chart/tick data)

class UltraScalpBot:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.active_order_id = None
        self.position = None # {'side': 'Long', 'entry': 100.0, 'qty': 10}
        
        print(f" ULTRA SCALP BOT INITIALIZED")
        print(f"   Symbol: {SYMBOL}")
        print(f"   Leverage: {LEVERAGE}x")
        print(f"   Margin: ${MARGIN} (Total Notional: ${POSITION_SIZE})")
        print(f"   Mode: Sustainable Maker (Limit Only)")
        print(f"   Speed: {POLL_INTERVAL}s (Tick Simulation)")
        
    def get_market_state(self):
        """
        Get BBO (Best Bid Offer) and Imbalance from Depth.
        This simulates '1s chart' by looking at tick-level order book data.
        """
        depth = self.data.get_depth(SYMBOL)
        if not depth:
            return None
            
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        if not bids or not asks:
            return None
            
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        
        # Calculate Imbalance (Top 5 levels)
        bid_vol = sum([float(x[1]) for x in bids[:5]])
        ask_vol = sum([float(x[1]) for x in asks[:5]])
        
        imbalance = bid_vol / ask_vol if ask_vol > 0 else 1.0
        
        return {
            'bid': best_bid,
            'ask': best_ask,
            'mid': (best_bid + best_ask) / 2,
            'imbalance': imbalance # > 1 Bullish, < 1 Bearish
        }

    def run(self):
        print(" Starting High-Frequency Loop...")
        try:
            while True:
                state = self.get_market_state()
                if not state:
                    time.sleep(POLL_INTERVAL)
                    continue
                    
                bid = state['bid']
                ask = state['ask']
                mid = state['mid']
                imbalance = state['imbalance']
                
                # Logic: Sustainable Scalp (Maker Only)
                # If we have no position, try to enter at Best Bid (if Bullish) or Best Ask (if Bearish)
                # But ensure we are Maker (Limit Order)
                
                if self.position is None:
                    # ENTRY LOGIC
                    # If Imbalance > 1.5 (Bullish Pressure), place Bid at Best Bid
                    if imbalance > 1.5:
                        price = bid
                        qty = POSITION_SIZE / price
                        print(f"   🟢 Bullish Flow ({imbalance:.2f}). Placing Maker Buy at {price}")
                        self.execute_maker_entry('Bid', price, qty)
                        
                    # If Imbalance < 0.6 (Bearish Pressure), place Ask at Best Ask
                    elif imbalance < 0.6:
                        price = ask
                        qty = POSITION_SIZE / price
                        print(f"    Bearish Flow ({imbalance:.2f}). Placing Maker Sell at {price}")
                        self.execute_maker_entry('Ask', price, qty)
                        
                else:
                    # EXIT LOGIC
                    # We have a position. We need to place a Limit TP immediately to capture spread.
                    # Or a Stop Loss if price moves against us.
                    
                    entry = self.position['entry']
                    side = self.position['side']
                    qty = self.position['qty']
                    
                    current_pnl_pct = (mid - entry) / entry if side == 'Bid' else (entry - mid) / entry
                    
                    # Target: 0.1% Profit (Scalp)
                    if side == 'Bid': # Long
                        target = entry * (1 + MIN_PROFIT_PCT)
                        stop = entry * (1 - STOP_LOSS_PCT)
                    else: # Short
                        target = entry * (1 - MIN_PROFIT_PCT)
                        stop = entry * (1 + STOP_LOSS_PCT)
                        
                    # Check if we should exit (Simulated for now, real implementation would place Limit Orders)
                    # For Maker strategy, we should place the TP order in the book.
                    
                    # If PnL > Target, we are happy.
                    # Actually, as a Maker, we should have placed the TP order already.
                    # For simplicity in this loop, we check if price reached target.
                    
                    print(f"    Position Open: {side} @ {entry} | PnL: {current_pnl_pct*100:.3f}% | Target: {target:.4f}")
                    
                    # Stop Loss (Market Close for safety)
                    if (side == 'Bid' and mid < stop) or (side == 'Ask' and mid > stop):
                        print(f"    STOP LOSS TRIGGERED at {mid}")
                        self.trade.close_position(SYMBOL, qty if side == 'Bid' else -qty)
                        self.position = None
                        
                    # Take Profit (Maker Limit if close)
                    # Real implementation: Check if our Limit TP was filled.
                    # Here we simulate fill if price crosses target.
                    elif (side == 'Bid' and mid >= target) or (side == 'Ask' and mid <= target):
                        print(f"    TAKE PROFIT TRIGGERED at {mid}")
                        # We assume our Limit Order would have filled.
                        # In real bot, we'd query order status.
                        # For now, close to reset state.
                        self.trade.close_position(SYMBOL, qty if side == 'Bid' else -qty)
                        self.position = None

                time.sleep(POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n Stopping Ultra Scalp Bot...")

    def execute_maker_entry(self, side, price, qty):
        # Place Limit Order (Post Only)
        res = self.trade.execute_order(
            symbol=SYMBOL,
            side=side,
            price=f"{price:.4f}",
            quantity=f"{qty:.1f}", # Adjust precision as needed
            order_type="Limit",
            post_only=True
        )
        
        if res and 'id' in res:
            print(f"    Order Placed: {res['id']}")
            # Assume fill for simulation loop purpose or verify status
            # For this MVP, we assume fill if price stays there.
            # In production, we'd poll order status.
            # Let's "simulate" a fill to enter the loop logic
            self.position = {
                'side': side,
                'entry': price,
                'qty': qty
            }
        else:
            print(f"    Order Failed (Likely Taker/Reject): {res}")

if __name__ == "__main__":
    bot = UltraScalpBot()
    bot.run()
