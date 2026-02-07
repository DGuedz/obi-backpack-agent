
import os
import sys
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))
from core.backpack_transport import BackpackTransport
from core.technical_oracle import TechnicalOracle
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

class RecoveryCommander:
    def __init__(self):
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        
        # Configuration
        self.LEVERAGE = 5
        self.ALLOCATION_PCT = 0.70  # 70% of Equity
        self.MIN_PROFIT_PCT = 0.003 # 0.3% (Covers Fees ~0.12% + Spread + Small Profit)
        
    def scan_market(self):
        print("\n SCANNING MARKET (Simplified)...")
        tickers = self.data_client.get_tickers()
        if not tickers: return []
        
        perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
        perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        top_10 = perps[:10]
        
        results = []
        for t in top_10:
            symbol = t['symbol']
            try:
                # Use simplified OBI or Oracle if fast
                # Oracle might take time per asset
                obi = self.oracle.calculate_obi(symbol)
                results.append({
                    'symbol': symbol,
                    'obi': obi,
                    'score': 70 if abs(obi) > 0.1 else 40, # Simple score
                    'wave_status': 'Unknown'
                })
                print(f"   -> Scanned {symbol}: OBI {obi}")
            except Exception as e:
                print(f"   x Failed {symbol}: {e}")
        return results

    def execute_recovery_plan(self):
        print("\n RECOVERY STRATEGY: 70% ALLOCATION | 5x LEVERAGE")
        print("==================================================")
        
        # 1. Check Balance
        capital = self.transport.get_account_collateral()
        usdc_balance = 0
        total_equity = 0
        
        if capital:
            usdc_data = capital.get('USDC', {'available': '0'})
            usdc_balance = float(usdc_data.get('available', 0))
            # Estimate total equity (simplified)
            total_equity = usdc_balance 
            # (Add other assets if needed, but for opening perps we need USDC)
            
        print(f" AVAILABLE EQUITY: ${total_equity:.2f}")
        
        if total_equity < 5: # Min $5 to trade safely
            print(" CRITICAL: Insufficient funds to execute strategy.")
            return

        # 2. Calculate Position Size
        deployable_capital = total_equity * self.ALLOCATION_PCT
        total_notional = deployable_capital * self.LEVERAGE
        print(f" DEPLOYABLE CAPITAL: ${deployable_capital:.2f} (70%)")
        print(f" TOTAL NOTIONAL POWER: ${total_notional:.2f} (5x)")
        
        # 3. Find Targets
        print("\n SCANNING FOR TARGETS...")
        # Get top opportunities from scanner
        opportunities = self.scan_market()
        
        # Filter: Strong Signals Only (Score >= 70)
        targets = [op for op in opportunities if op['score'] >= 70]
        
        if not targets:
            print("️ No strong targets found. Expanding search...")
            targets = [op for op in opportunities if op['score'] >= 50]
            
        if not targets:
            print(" No valid targets found in market.")
            return

        # Select Top 3 to diversify
        selected_targets = targets[:3]
        num_targets = len(selected_targets)
        notional_per_trade = total_notional / num_targets
        
        print(f"\n SELECTED TARGETS ({num_targets}):")
        for t in selected_targets:
            print(f"   - {t['symbol']} | OBI: {t['obi']}")
            
        confirm = input(f"\n EXECUTE {num_targets} TRADES @ ${notional_per_trade:.2f} EACH? (y/n): ")
        if confirm.lower() != 'y':
            print(" Execution aborted by user.")
            return

        # 4. Execute Trades
        for target in selected_targets:
            symbol = target['symbol']
            side = "Buy" if target['obi'] > 0 else "Sell" # Simplified OBI logic
            
            print(f"\n EXECUTING {side.upper()} on {symbol}...")
            
            # Get current price
            ticker = self.transport.get_ticker(symbol)
            if not ticker:
                print(f"    Price check failed for {symbol}")
                continue
                
            price = float(ticker['lastPrice'])
            quantity = notional_per_trade / price
            
            # Round quantity (heuristic)
            if price > 100: quantity = round(quantity, 3)
            elif price > 1: quantity = round(quantity, 1)
            else: quantity = int(quantity)
            
            # Execute Market Order for Speed (Recovery Mode)
            
            # Calculate TP/SL prices
            if side == "Buy":
                tp_price = price * (1 + self.MIN_PROFIT_PCT)
                sl_price = price * (1 - 0.02) # 2% SL
            else:
                tp_price = price * (1 - self.MIN_PROFIT_PCT)
                sl_price = price * (1 + 0.02) # 2% SL
                
            print(f"    Plan: Entry ~{price} | TP: {tp_price:.4f} | SL: {sl_price:.4f}")
            
            # Execute
            result = self.transport.execute_order(
                symbol=symbol,
                order_type="Market",
                side=side,
                quantity=str(quantity)
            )
            
            if result:
                print(f"    ORDER EXECUTED! ID: {result.get('id', 'Unknown')}")
            else:
                print("    EXECUTION FAILED.")
                
        print("\n RECOVERY SEQUENCE COMPLETE.")

if __name__ == "__main__":
    commander = RecoveryCommander()
    commander.execute_recovery_plan()
