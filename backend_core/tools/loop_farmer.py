import time
import logging
import sys
import os

# Add project root to path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vsc_brain import VSCBrain

# Mock Client/Oracle for structure (User can replace with actual)
class MockMarketData:
    @staticmethod
    def get_data(symbol):
        # Simulating a valid entry scenario
        return {
            'price': 100.0,
            'funding': 0.0001,  # Low funding (Neutral/Good)
            'netflow': -6000000, # Outflow > 5M (Bullish)
            'oi_delta': 0.03,   # Stable/Growing
            'rsi': 45,          # Healthy pullback level
            'obi': 0.1          # Slight Buy Wall
        }

class LoopFarmer:
    """
    Loop Farmer - Main Execution Unit.
    Flow: Strategy -> Protocol Zero -> VSC Brain -> Execution.
    """
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("LoopFarmer")
        self.brain = VSCBrain()
        self.data_source = MockMarketData()
        self.logger.info(" Loop Farmer Initialized with VSC Brain Architecture")

    def protocol_zero_check(self, symbol):
        """
        Protocol Zero: Survival Filter.
        Checks basic risk parameters (Max Drawdown, Daily Loss, etc.)
        """
        # Logic to read tools/protocolo_zero_config.vsc would go here
        # For now, assume PASSED
        return True

    def load_targets(self):
        """
        Loads targets from tools/loop_targets.vsc
        Format: SYMBOL,DIRECTION_BIAS
        """
        targets = []
        try:
            with open("tools/loop_targets.vsc", "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(',')
                    if len(parts) >= 2:
                        targets.append({"symbol": parts[0], "bias": parts[1]})
        except FileNotFoundError:
            self.logger.error("Target file not found. Using default.")
            targets = [{"symbol": "SOL_USDC", "bias": "NEUTRAL"}]
        return targets

    def get_available_margin(self):
        """
        Simulates fetching available (free) margin from the exchange.
        In production, this would call: self.exchange.get_balance()['USDC']['free']
        """
        # Simulating $1,250.00 of idle USDC waiting for work
        return 1250.00 

    def run_multi_cycle(self):
        targets = self.load_targets()
        available_margin = self.get_available_margin()
        target_count = len(targets)
        
        if target_count == 0:
            self.logger.warning("No targets found. Sleeping.")
            return

        # Divide a margem disponível igualmente entre os alvos ativos
        # Ex: $1250 / 5 ativos = $250 por ativo
        allocation_per_asset = available_margin / target_count
        
        self.logger.info(f" Starting Multi-Asset Cycle on {target_count} assets")
        self.logger.info(f" Available Margin: ${available_margin:.2f} | Allocating ${allocation_per_asset:.2f} per asset")
        
        for target in targets:
            symbol = target['symbol']
            bias = target['bias']
            self.run_cycle(symbol, bias, allocation_per_asset)
            time.sleep(0.5) # Throttle

    def run_cycle(self, symbol, bias="NEUTRAL", base_size=10.0):
        self.logger.info(f"--- Cycling {symbol} (Bias: {bias}) ---")
        
        # 1. PERCEPTION (Data Gathering)
        market_data = self.data_source.get_data(symbol)
        self.logger.info(f" Market Data: RSI={market_data['rsi']}, Funding={market_data['funding']}, Netflow={market_data['netflow']}")
        
        # 2. STRATEGY INTENT
        # If bias is NEUTRAL, we assume LONG for simulation purposes or dynamic logic
        intent_direction = "LONG" if bias in ["NEUTRAL", "LONG"] else "SHORT"
        
        # Override for specific simulation logic if needed
        self.logger.info(f" Strategy proposes: {intent_direction}")

        # 3. PROTOCOL ZERO (Survival Gate)
        if not self.protocol_zero_check(symbol):
            self.logger.warning(" Protocol Zero triggered. Aborting.")
            return

        # 4. VSC BRAIN (Cognitive Gate)
        approved, reason, size_factor = self.brain.validate_entry(symbol, intent_direction, market_data)

        if approved:
            self.execute_order(symbol, intent_direction, reason, size_factor, base_size)
        else:
            self.logger.info(f" Brain VETO: {reason}")

    def execute_order(self, symbol, direction, reason, size_factor, base_size):
        # O tamanho final é ajustado pelo "fator de confiança" do cérebro (Microsize vs Full)
        final_size = base_size * size_factor
        self.logger.info(f" EXECUTING {direction} on {symbol} | Size: ${final_size:.2f} (Base: ${base_size:.2f} * Factor: {size_factor}) | Reason: {reason}")
        # Real execution logic here

if __name__ == "__main__":
    farmer = LoopFarmer()
    # Execute Multi-Asset Loop
    farmer.run_multi_cycle()
