
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

class FineLineSniper:
    def __init__(self):
        self.symbol = "IP_USDC_PERP"
        self.leverage = 10
        self.budget = 100
        
        # Fine Line Parameters (Front-Running Whales)
        self.OB_IMBALANCE_THRESHOLD = 2.0 # 2x Sell Pressure -> Short
        self.VOLUME_SPIKE_THRESHOLD = 3.0 # 3x Avg Volume -> Action
        
        # State
        self.last_action = None
        self.cooldown = 0

    def scan_market(self):
        print(f" FINE LINE SNIPER: Scanning {self.symbol}...")
        
        # 1. Order Book Analysis (The "Intent")
        depth = data.get_depth(self.symbol)
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        bid_vol = sum([float(x[1]) for x in bids[:10]]) # Top 10 levels
        ask_vol = sum([float(x[1]) for x in asks[:10]])
        
        imbalance = ask_vol / bid_vol if bid_vol > 0 else 10
        
        print(f"    Order Book Imbalance: {imbalance:.2f} (Ask/Bid)")
        
        if imbalance > self.OB_IMBALANCE_THRESHOLD:
            print("    WHALE DETECTED: Heavy Sell Wall building up!")
            return "SELL_SIGNAL"
            
        elif imbalance < (1 / self.OB_IMBALANCE_THRESHOLD):
            print("    WHALE DETECTED: Heavy Buy Support incoming!")
            return "BUY_SIGNAL"
            
        # 2. Tape Reading (Recent Trades) - Not available in public REST easily, using 1m Volume
        klines = data.get_klines(self.symbol, interval="1m", limit=5)
        last_vol = float(klines[-1]['volume'])
        avg_vol = sum([float(x['volume']) for x in klines[:-1]]) / 4
        
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1
        print(f"    Volume Ratio: {vol_ratio:.2f}x")
        
        if vol_ratio > self.VOLUME_SPIKE_THRESHOLD:
            # Check candle color
            open_p = float(klines[-1]['open'])
            close_p = float(klines[-1]['close'])
            if close_p < open_p:
                print("    VOLUME SPIKE (RED): Dumping initiated.")
                return "SELL_SIGNAL"
            else:
                print("    VOLUME SPIKE (GREEN): Pumping initiated.")
                return "BUY_SIGNAL"
                
        return "WAIT"

    def execute(self, signal):
        if signal == "WAIT":
            return
            
        print(f"️ EXECUTION TRIGGERED: {signal}")
        
        # Determine Side
        side = "Ask" if signal == "SELL_SIGNAL" else "Bid"
        side_txt = "SHORT" if signal == "SELL_SIGNAL" else "LONG"
        
        # Calculate Qty
        ticker = data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        notional = self.budget * self.leverage
        qty = round(notional / price, 1)
        
        print(f"    Front-Running Whales: {side_txt} {qty} IP @ {price}")
        
        # Execute Market (Speed is key for front-running)
        res = trade.execute_order(
            symbol=self.symbol,
            side=side,
            price=None,
            quantity=str(qty),
            order_type="Market"
        )
        
        if res and 'id' in res:
            print(f"    ORDER FILLED: {res['id']}")
            # Immediate TP/SL (Scalp)
            self.deploy_safety(side, price, qty)
        else:
            print(f"    Execution Failed: {res}")

    def deploy_safety(self, side, entry_price, qty):
        # Very Tight Scalp (Front-run exit too)
        # TP: 1.0% (Quick slice)
        # SL: 0.8% (Tight risk)
        
        if side == "Bid": # Long
            tp = entry_price * 1.01
            sl = entry_price * 0.992
            exit_side = "Ask"
        else: # Short
            tp = entry_price * 0.99
            sl = entry_price * 1.008
            exit_side = "Bid"
            
        print(f"   ️ Safety: TP {tp:.4f} | SL {sl:.4f}")
        
        # TP
        trade.execute_order(self.symbol, exit_side, f"{tp:.4f}", str(qty), "Limit", reduce_only=True)
        # SL (Trigger Limit)
        # Simplified for speed
        
if __name__ == "__main__":
    bot = FineLineSniper()
    while True:
        try:
            sig = bot.scan_market()
            if sig != "WAIT":
                bot.execute(sig)
                break # Exit after 1 trade for safety review
            time.sleep(2) # Fast scan
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
