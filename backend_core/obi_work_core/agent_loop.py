import time
import sys
import os
import argparse
import logging
import signal
import resource
from datetime import datetime

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

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [OBI-CORE] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class AgentLoop:
    """
    OBI WORK CORE - Main Execution Loop (Institutional Grade)
    Orchestrates Identity, Context, Risk, Execution, and On-Chain Audit.
    Includes Safety mechanisms: Resource Limits, Signal Handling, and Backoff.
    """
    
    def __init__(self, vsc_file: str, mode: str = 'standard', timeout: int = 30):
        logger.info(f"Initializing OBI WORK Agent Loop (Mode: {mode.upper()})...")
        self.mode = mode
        self.timeout = timeout
        self.running = True
        self.last_tick = time.time()
        
        # Setup Signal Handlers
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

        # 1. Identity
        self.identity = AgentIdentity()
        logger.info(f"Identity Established: {self.identity.session_id}")
        
        # 2. Context Load
        self.loader = ExecutionContextLoader(vsc_file)
        self.context = self.loader.load()
        logger.info(f"Context Loaded: {self.context.get('risk_profile', 'UNKNOWN')}")
        
        # 3. Intent Translation
        self.translator = IntentTranslator(self.context)
        self.strategy_config = self.translator.translate()
        logger.info(f"Strategy Configured: {self.strategy_config}")
        
        # 4. Infrastructure
        self.client = BackpackClient()
        self.solana_signer = SolanaSigner()
        
        # 5. Risk Engine Setup
        self.risk_engine = RiskDesignEngine(self.context)
        
        # Fetch real balance or fallback
        current_balance = 1000.0 
        try:
            # self.client.get_balance() would go here
            pass 
        except Exception as e:
            logger.warning(f"Balance fetch failed: {e}. Using fallback.")
            
        self.constraints = self.risk_engine.generate_constraints(current_balance=current_balance)
        self.gatekeeper = RiskGatekeeper(self.constraints)
        logger.info(f"Risk Constraints Applied: {self.constraints}")
        
    def _shutdown_handler(self, signum, frame):
        logger.info(f"Signal {signum} received. Initiating Graceful Shutdown...")
        self.running = False

    def run(self):
        logger.info("--- ENTERING EXECUTION LOOP ---")
        consecutive_errors = 0
        
        while self.running:
            try:
                loop_start = time.time()
                
                # Watchdog Check (Internal)
                if loop_start - self.last_tick > self.timeout:
                    logger.warning("Lag detected in execution cycle.")
                
                self._cycle()
                
                # Reset error counter on success
                consecutive_errors = 0
                self.last_tick = time.time()
                
                # Rate Limit / HFT Pacing
                time.sleep(0.5) 
                
            except KeyboardInterrupt:
                self._shutdown_handler(signal.SIGINT, None)
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Cycle Error: {e}")
                
                # Backoff Logic
                backoff_time = min(2 ** consecutive_errors, 60)
                logger.info(f"Backing off for {backoff_time}s...")
                time.sleep(backoff_time)
                
                if consecutive_errors > 5:
                    logger.critical("Too many consecutive errors. Aborting.")
                    self.running = False

        self._finalize()

    def _finalize(self):
        logger.info("--- SHUTDOWN SEQUENCE ---")
        logger.info("Generating Final Audit Receipt...")
        try:
            receipt = self.identity.get_identity_receipt()
            logger.info(f"Receipt Generated: {receipt.get('signature', 'UNSIGNED')[:10]}...")
        except Exception as e:
            logger.error(f"Failed to generate receipt: {e}")
        logger.info("Agent Stopped Safely.")

    def _cycle(self):
        """Single Execution Cycle"""
        # A. Integrity Check
        if not self.identity.validate_integrity():
            logger.critical("INTEGRITY FAILURE. ABORTING.")
            self.running = False
            return
            
        # B. Market Scan & Execution per Asset
        assets = self.context.get('assets', [])
        for asset in assets:
            symbol = f"{asset}_USDC" if "_" not in asset else asset
            self._process_asset(symbol)
            
    def _process_asset(self, symbol: str):
        # 1. Fetch Data
        try:
            candles = self.client.get_candles(symbol, self.strategy_config.timeframe, limit=50)
            ticker = self.client.get_ticker(symbol)
            
            if not candles or not ticker:
                return

            # 2. Analyze
            rsi = MarketAnalyzer.calculate_rsi(candles)
            
            market_data = {
                "symbol": symbol,
                "best_bid": float(ticker.get('bestBid', 0)),
                "best_ask": float(ticker.get('bestAsk', 0)),
                "rsi": rsi
            }
            
            # 3. Evaluate
            signal = self._evaluate_signal(market_data)
            
            if signal:
                logger.info(f"[{symbol}] Signal Detected: {signal['side']} @ RSI {rsi:.1f}")
                
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
                    logger.warning(f"GATEKEEPER VETO: {reason}")

        except Exception as e:
            logger.debug(f"Asset processing error ({symbol}): {e}")
            raise e # Re-raise to trigger backoff in main loop

    def _evaluate_signal(self, data: dict):
        """Simple RSI Strategy"""
        rsi = data['rsi']
        if rsi < 30:
            return {
                "symbol": data['symbol'],
                "side": "Buy",
                "size": 10.0, # Example fixed size
                "leverage": 1,
                "price": data['best_ask']
            }
        elif rsi > 70:
            return {
                "symbol": data['symbol'],
                "side": "Sell",
                "size": 10.0,
                "leverage": 1,
                "price": data['best_bid']
            }
        return None

    def _execute(self, signal: dict):
        """Execute Order via Backpack Client"""
        logger.info(f"EXECUTING: {signal['side']} {signal['symbol']} ${signal['size']}")
        # In real production, this calls self.client.execute_order(...)
        # For now, we simulate execution log
        self.solana_signer.sign_audit_receipt(signal)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OBI WORK Agent Executor')
    parser.add_argument('--vsc', type=str, default='VSC_INFRA_RULES.txt', help='Path to VSC instruction file')
    parser.add_argument('--mode', type=str, default='standard', choices=['standard', 'safe', 'aggressive'], help='Execution mode')
    parser.add_argument('--max-workers', type=int, default=1, help='Max thread workers')
    parser.add_argument('--timeout', type=int, default=30, help='Cycle timeout in seconds')
    parser.add_argument('--memory-limit', type=int, default=512, help='Memory limit in MB')
    parser.add_argument('--cpu-limit', type=int, default=1, help='CPU Core affinity (not strict limit in python)')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')

    args = parser.parse_args()
    
    # Set Logging Level
    logger.setLevel(getattr(logging, args.log_level.upper()))
    
    # Set Resource Limits (Unix only)
    try:
        # Limit Memory (Soft and Hard limit)
        mem_limit_bytes = args.memory_limit * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_limit_bytes, mem_limit_bytes))
        logger.info(f"Memory Limit set to {args.memory_limit}MB")
    except Exception as e:
        logger.warning(f"Could not set resource limits: {e}")

    agent = AgentLoop(vsc_file=args.vsc, mode=args.mode, timeout=args.timeout)
    agent.run()
            
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
