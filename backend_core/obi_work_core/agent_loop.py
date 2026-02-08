import time
import sys
import os

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.agent_identity import AgentIdentity
from obi_work_core.context_loader import ExecutionContextLoader
from obi_work_core.risk_engine import RiskDesignEngine
from obi_work_core.risk_gatekeeper import RiskGatekeeper
from obi_work_core.intent_translator import IntentTranslator
from obi_work_core.backpack_client import BackpackClient
from obi_work_core.market_analyzer import MarketAnalyzer
from obi_work_core.solana_signer import SolanaSigner

class AgentLoop:
    """
    OBI WORK CORE - Main Execution Loop
    Orchestrates Identity, Context, Risk, Execution, and On-Chain Audit.
    """
    
    def __init__(self, vsc_file: str):
        print("Initializing OBI WORK Agent Loop...")
        
        # 1. Identity
        self.identity = AgentIdentity()
        print(f"Identity Established: {self.identity.session_id}")
        
        # 2. Context Load
        self.loader = ExecutionContextLoader(vsc_file)
        self.context = self.loader.load()
        print(f"Context Loaded: {self.context['risk_profile']}")
        
        # 3. Intent Translation
        self.translator = IntentTranslator(self.context)
        self.strategy_config = self.translator.translate()
        print(f"Strategy Configured: {self.strategy_config}")
        
        # 4. Infrastructure
        self.client = BackpackClient()
        self.solana_signer = SolanaSigner()
        
        # 5. Risk Engine Setup
        self.risk_engine = RiskDesignEngine(self.context)
        
        # Fetch real balance or fallback
        # In production, fetch 'USDC' balance
        current_balance = 1000.0 # Default fallback
        try:
            # Simple check, assuming 1000 if fails for now to avoid blocking logic without keys
            # In real scenario, use self.client.get_balance()
            pass 
        except:
            pass
            
        self.constraints = self.risk_engine.generate_constraints(current_balance=current_balance)
        self.gatekeeper = RiskGatekeeper(self.constraints)
        print(f"Risk Constraints Applied: {self.constraints}")
        
    def run(self):
        print("\n--- ENTERING EXECUTION LOOP (Ctrl+C to Stop) ---")
        try:
            while True:
                self._cycle()
                time.sleep(0.5) # 0.5s Loop (HFT Optimization)
        except KeyboardInterrupt:
            print("\n--- SHUTDOWN SEQUENCE INITIATED ---")
            print("Generating Final Audit Receipt...")
            print(self.identity.get_identity_receipt())
            print("Done.")

    def _cycle(self):
        """Single Execution Cycle"""
        # A. Integrity Check
        if not self.identity.validate_integrity():
            print("CRITICAL: INTEGRITY FAILURE. ABORTING.")
            sys.exit(1)
            
        # B. Market Scan & Execution per Asset
        assets = self.context.get('assets', [])
        for asset in assets:
            symbol = f"{asset}_USDC" if "_" not in asset else asset
            self._process_asset(symbol)
            
    def _process_asset(self, symbol: str):
        # 1. Fetch Data (Candles + Ticker for Best Bid/Ask)
        candles = self.client.get_candles(symbol, self.strategy_config.timeframe, limit=50)
        ticker = self.client.get_ticker(symbol)
        
        if not candles or not ticker:
            print(f"X", end="", flush=True)
            return

        # 2. Analyze
        rsi = MarketAnalyzer.calculate_rsi(candles)
        
        # Use Ticker Best Bid/Ask if available, fallback to lastPrice
        best_bid = float(ticker.get('bestBid', ticker.get('lastPrice')))
        best_ask = float(ticker.get('bestAsk', ticker.get('lastPrice')))
        
        market_data = {
            "symbol": symbol,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "rsi": rsi
        }
        
        # 3. Evaluate
        signal = self._evaluate_signal(market_data)
        
        if signal:
            print(f"\n[{symbol}] Signal Detected: {signal['side']} @ RSI {rsi:.1f}")
            
            # 4. Risk Gatekeeper Check
            allowed, reason = self.gatekeeper.check_order(
                symbol=signal['symbol'],
                side=signal['side'],
                size_usd=signal['size'],
                leverage=signal['leverage']
            )
            
            if allowed:
                self._execute(signal)
            else:
                print(f" GATEKEEPER VETO: {reason}")
        else:
            # Heartbeat (Quiet)
            pass
            
    def _evaluate_signal(self, data: dict):
        """Simple evaluator based on translated config."""
        # Buy Logic
        if data['rsi'] < self.strategy_config.rsi_buy:
            # OPTIMIZATION: Use Best Bid for Maker execution (or Limit Chasing)
            # If Aggressive, we might want to cross spread (Taker) -> Best Ask
            # But user requested "Spread Capture" -> Best Bid
            entry_price = data['best_bid']
            
            return {
                "symbol": data['symbol'],
                "side": "Bid", 
                "size": self.constraints['max_entry_size_usd'],
                "price": entry_price,
                "leverage": 1 
            }
        # Sell Logic (Simplified)
        elif data['rsi'] > self.strategy_config.rsi_sell:
             entry_price = data['best_ask']
             return {
                "symbol": data['symbol'],
                "side": "Ask",
                "size": self.constraints['max_entry_size_usd'],
                "price": entry_price,
                "leverage": 1 
            }
        return None
        
    def _execute(self, signal: dict):
        """Execution and Audit"""
        print(f">>> EXECUTING {signal['side']} {signal['symbol']} | Size: ${signal['size']:.2f}")
        
        # Calculate quantity (Base Asset)
        # Round to 2 decimals for simplicity (should use step size in real prod)
        quantity = round(signal['size'] / signal['price'], 2)
        
        if quantity <= 0:
            print("Quantity too small.")
            return

        # Execute via Client
        result = self.client.execute_order(
            symbol=signal['symbol'],
            side=signal['side'],
            order_type=self.strategy_config.order_type,
            quantity=quantity
            # price=... (if Limit)
        )
        
        if result:
            # Audit
            receipt = {
                "session_id": self.identity.session_id,
                "timestamp": time.time(),
                "signal": signal,
                "strategy": str(self.strategy_config),
                "integrity_hash": self.identity.identity_hash,
                "tx_id": result.get('id', 'unknown')
            }
            
            # Sign Receipt (Agent Identity)
            signature = self.solana_signer.sign_audit_receipt(receipt)
            receipt['signature'] = signature
            
            print(f" AUDIT RECEIPT SIGNED: {receipt['signature'][:16]}...")
            
            # Publish On-Chain (Optional/Async in Prod)
            if self.context.get('audit_enabled', False):
                tx_sig = self.solana_signer.publish_onchain(receipt)
                print(f" PROOF OF VOLUME PUBLISHED: {tx_sig}")
            
        else:
            print(" EXECUTION FAILED (API Error)")

if __name__ == "__main__":
    import sys
    
    # Use provided VSC file or default to runtime_context.vsc
    vsc_file = sys.argv[1] if len(sys.argv) > 1 else "runtime_context.vsc"
    
    # Ensure default exists if needed
    if vsc_file == "runtime_context.vsc" and not os.path.exists(vsc_file):
        with open(vsc_file, "w") as f:
            f.write("risk_profile: aggressive\nassets: [SOL]\nmax_loss_usd: 100.0\nallow_short: true")
            
    agent = AgentLoop(vsc_file)
    agent.run()
