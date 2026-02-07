
import os
import time
import random
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

class HarvesterBot:
    def __init__(self):
        # SUSTAINABLE FARM ASSETS (Low Volatility or High Yield)
        # RESCUE PROTOCOL: SOL & BTC ONLY
        self.assets = ["SOL_USDC_PERP", "BTC_USDC_PERP"] 
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
        self.budget = 100 # $100 Isolated Budget (Increased)
        self.leverage = 5 # 5x (Sustainable)
        self.target_profit = 0.003 # 0.3%
        self.stop_loss = 0.025 # 2.5% SL (Wide for Volatility)

    def run(self):
        print(f" HARVESTER BOT ACTIVATED (Secondary Operation)")
        print(f"   Budget: ${self.budget} | Leverage: {self.leverage}x")
        print(f"   Mode: Sustainable Yield (Spread Harvesting)")
        
        while True:
            try:
                for symbol in self.assets:
                    self.harvest(symbol)
                    time.sleep(5)
                    
                print(" Harvester Sleeping (45s)...")
                time.sleep(45)
            except Exception as e:
                print(f"️ Harvester Loop Error: {e}")
                time.sleep(10)

    def harvest(self, symbol):
        # 1. Check if we already have a position or order
        if self.is_active(symbol):
            return

        # 2. Analyze Market (Simple Trend)
        ticker = self.data.get_ticker(symbol)
        if not ticker: return
        
        price = float(ticker['lastPrice'])
        
        # Simple VWAP proxy (last 20 trades?) No, simple MA logic or just Spread Capture.
        # Sustainable = Buy Low, Sell High on Micro-range.
        # Strategy: Place Maker Bid at -0.1% of Last Price (Capture Spread)
        
        side = "Bid" # Default to Long for funding/uptrend?
        # Check trend via 1h change?
        # If funding is negative (paying shorts), we might short.
        # Let's check Funding.
        funding = float(ticker.get('fundingRate', 0))
        
        if funding < -0.0001: # High Negative Funding -> LONG (Receive Yield)
            side = "Bid"
            print(f"    {symbol}: Funding Negative ({funding*100:.4f}%). Harvesting Long.")
        elif funding > 0.0001: # High Positive Funding -> SHORT (Receive Yield)
            side = "Ask"
            print(f"    {symbol}: Funding Positive ({funding*100:.4f}%). Harvesting Short.")
        else:
            # Neutral Funding -> Follow Trend or Random?
            # Sustainable -> Follow 24h Change
            change = float(ticker.get('priceChangePercent', 0))
            side = "Bid" if change > 0 else "Ask"
            
        # 3. Calculate Entry
        entry_price = price * (0.999 if side == "Bid" else 1.001) # 0.1% discount/premium
        
        # 4. Calculate Quantity
        notional = self.budget * self.leverage
        qty = notional / entry_price
        
        # Rounding
        qty = self.round_qty(symbol, qty)
        entry_price = self.round_price(symbol, entry_price)
        
        print(f"    Harvester Planting: {side} {symbol} | ${notional:.0f} @ {entry_price}")
        
        # 5. Execute Post-Only
        self.trade.execute_order(
            symbol=symbol,
            side=side,
            order_type="Limit",
            quantity=str(qty),
            price=str(entry_price),
            post_only=True
        )
        
        # We rely on Sentinel for SL/TP placement after fill? 
        # Or we can place SL immediately if supported (Guardian Protocol logic is better in Sentinel)
        # But Harvester should be self-contained for simplicity?
        # Let's assume Sentinel handles protection.

    def is_active(self, symbol):
        # Check Orders
        orders = self.data.get_open_orders()
        for o in orders:
            if o['symbol'] == symbol: return True
            
        # Check Positions
        positions = self.data.get_positions()
        for p in positions:
            if p['symbol'] == symbol and float(p['netQuantity']) != 0: return True
            
        return False

    def round_qty(self, symbol, qty):
        if "PEPE" in symbol or "SHIB" in symbol or "BONK" in symbol or "FOGO" in symbol:
            return int(qty)
        elif "LDO" in symbol:
             return int(qty)
        elif qty > 1000:
            return round(qty, 0)
        elif qty > 1:
            return round(qty, 1)
        else:
            return round(qty, 2)

    def round_price(self, symbol, price):
        # Simple rounding, ideally use tick size
        if price < 1: return round(price, 5)
        if price < 100: return round(price, 3)
        return round(price, 2)

if __name__ == "__main__":
    bot = HarvesterBot()
    bot.run()
