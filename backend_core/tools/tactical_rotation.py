import os
import sys
import time
import requests
from dotenv import load_dotenv

# Add project root and legacy archive to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

# Load environment variables
load_dotenv()

class TacticalRotation:
    def __init__(self):
        self.api_key = os.getenv("BACKPACK_API_KEY")
        self.api_secret = os.getenv("BACKPACK_API_SECRET")
        self.auth = BackpackAuth(self.api_key, self.api_secret)
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.min_profit_pct = 0.005 # 0.5% target to "pay bills" and rotate

    def get_positions(self):
        try:
            positions = self.data.get_positions()
            print(f"DEBUG: Raw positions data: {positions}")
            # Filter for active positions (quantity != 0)
            return {p['symbol']: p for p in positions if float(p['quantity']) != 0}
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}

    def get_open_orders(self):
        try:
            orders = self.data.get_open_orders()
            print(f"DEBUG: Open Orders: {orders}")
            return orders
        except Exception as e:
            print(f"Error getting open orders: {e}")
            return []

    def get_market_price(self, symbol):
        try:
            # Using public API for speed
            url = f"https://api.backpack.exchange/api/v1/ticker?symbol={symbol}"
            response = requests.get(url)
            data = response.json()
            return float(data['lastPrice'])
        except:
            return 0.0

    def cleanup_orphans(self, positions, open_orders):
        print("\n CLEANUP PROTOCOL STARTED...")
        active_symbols = set(positions.keys())
        
        for order in open_orders:
            symbol = order['symbol']
            if symbol not in active_symbols:
                print(f"   -> Found ORPHAN order for {symbol} (No Position). Cancelling...")
                try:
                    self.trade.cancel_open_order(symbol, order['id'])
                    print(f"       Cancelled order {order['id']}")
                except Exception as e:
                    print(f"       Failed to cancel: {e}")

    def rotate_winners(self, positions):
        print("\n ROTATION PROTOCOL (CHECKING WINNERS)...")
        
        for symbol, pos in positions.items():
            entry_price = float(pos['entryPrice'])
            quantity = float(pos['quantity'])
            side = "LONG" if quantity > 0 else "SHORT"
            current_price = self.get_market_price(symbol)
            
            if current_price == 0:
                print(f"   ️ Could not get price for {symbol}")
                continue

            # Calculate PnL %
            if side == "LONG":
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price

            print(f"   -> {symbol} ({side}): Entry {entry_price} | Curr {current_price} | PnL: {pnl_pct*100:.2f}%")

            if pnl_pct >= self.min_profit_pct:
                print(f"       TARGET HIT (>0.5%). CLOSING TO ROTATE...")
                try:
                    # Close Market
                    exit_side = "Sell" if side == "LONG" else "Buy"
                    self.trade.execute_order(
                        symbol=symbol,
                        side=exit_side,
                        price="0",
                        quantity=abs(quantity),
                        order_type="Market"
                    )
                    print(f"       CLOSED {symbol} at Market. PnL Locked.")
                except Exception as e:
                    print(f"       Failed to close {symbol}: {e}")
            else:
                print(f"      ⏳ Holding (Target: 0.5%)")

    def execute(self):
        print(" TACTICAL ROTATION AGENT INITIALIZED")
        
        # 1. Get Data
        positions = self.get_positions()
        open_orders = self.get_open_orders()
        
        print(f" Active Positions: {list(positions.keys())}")
        
        # 2. Cleanup Orphans
        self.cleanup_orphans(positions, open_orders)
        
        # 3. Rotate Winners
        self.rotate_winners(positions)
        
        print("\n TACTICAL ROTATION COMPLETE")

if __name__ == "__main__":
    agent = TacticalRotation()
    agent.execute()
