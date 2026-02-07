import os
import time
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# --- CONFIG ---
BTC_SYMBOL = "BTC_USDC_PERP"
HEDGE_ASSETS = ["ETH_USDC_PERP", "SOL_USDC_PERP"] # Assets to Short

class HedgeManager:
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
    def calculate_hedge_requirement(self):
        """
        Calculates how much Short exposure is needed to neutralize BTC Longs.
        """
        try:
            positions = self.data.get_positions()
            
            # 1. Get BTC Long Exposure
            btc_pos = [p for p in positions if p['symbol'] == BTC_SYMBOL]
            if not btc_pos:
                print("   ℹ️ No BTC Position to Hedge.")
                return 0.0
                
            pos = btc_pos[0]
            if pos['side'].lower() != 'long':
                print("   ℹ️ BTC Position is Short (Self-Hedged).")
                return 0.0
                
            # Notional Value = Price * Quantity
            # Or use 'notional' if API provides, usually we calc manually
            # Assume entryPrice * quantity is roughly exposure
            btc_qty = float(pos.get('quantity', 0))
            btc_price = float(pos.get('markPrice', 0)) # Better than entry for current value
            btc_exposure = btc_qty * btc_price
            
            print(f"    BTC Long Exposure: ${btc_exposure:,.2f}")
            
            # 2. Check Existing Hedges
            current_hedge_value = 0.0
            for p in positions:
                if p['symbol'] in HEDGE_ASSETS and p['side'].lower() == 'short':
                    qty = float(p.get('quantity', 0))
                    price = float(p.get('markPrice', 0))
                    val = qty * price
                    current_hedge_value += val
                    
            print(f"   ️ Current Short Hedge: ${current_hedge_value:,.2f}")
            
            # 3. Net Exposure
            net_exposure = btc_exposure - current_hedge_value
            
            # Hedge Ratio: How much to cover? 50%? 100%?
            # In crash mode (Trend Broken), we want 100% coverage (Delta Neutral).
            # Or at least 50% to stop bleeding.
            # Let's target 50% Hedge initially to avoid over-hedging on wicks.
            
            target_hedge = btc_exposure * 0.50 
            needed_hedge = target_hedge - current_hedge_value
            
            return needed_hedge
            
        except Exception as e:
            print(f"    Hedge Calc Error: {e}")
            return 0.0

    def execute_hedge(self):
        print("\n️ [HEDGE MANAGER] Analyzing Delta Neutrality...")
        
        needed_usdc = self.calculate_hedge_requirement()
        
        if needed_usdc <= 50.0: # Minimum threshold to act
            print("    Portfolio is Balanced (or Hedge not needed).")
            return
            
        print(f"   ️ HEDGE DEFICIT: ${needed_usdc:,.2f}")
        print("    Executing Short Hedges on ETH/SOL...")
        
        # Split hedge between ETH and SOL for diversification
        # 50% ETH, 50% SOL
        split_amt = needed_usdc / 2.0
        
        for symbol in HEDGE_ASSETS:
            try:
                # Get Price
                ticker = self.data.get_ticker(symbol)
                price = float(ticker.get('lastPrice', 0))
                if price == 0: continue
                
                qty = split_amt / price
                qty = round(qty, 2) # Adjust precision based on asset (SOL 2, ETH 3?)
                if symbol == "ETH_USDC_PERP": qty = round(qty, 3)
                
                print(f"      -> Shorting {qty} {symbol} (~${split_amt:.2f})...")
                
                # Execute Market Short (Urgent Protection)
                # Or Limit IOC. Market is safer for Hedge.
                self.trade.execute_order(symbol, "Ask", 0, qty, order_type="Market")
                
            except Exception as e:
                print(f"       Failed to hedge {symbol}: {e}")

if __name__ == "__main__":
    hm = HedgeManager()
    hm.execute_hedge()
