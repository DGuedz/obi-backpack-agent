import os
import sys
import asyncio
import logging
import random
import argparse
from dotenv import load_dotenv

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE')) # Required for backpack_data

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("volume_farmer.log"),
        logging.StreamHandler()
    ]
)

class VolumeFarmer:
    def __init__(self, symbols=["ZORA_USDC_PERP"], leverage=10, dry_run=False, mode="straddle", direction="long", obi_threshold=0.20, target_pos_size_usd=30.0, target_profit_usd=0.04, max_slots=1, night_mode=False):
        load_dotenv()
        self.active_symbols = symbols[:max_slots] 
        self.candidate_pool = symbols 
        self.max_slots = max_slots
        self.leverage = leverage
        self.dry_run = dry_run
        self.mode = mode 
        self.direction = direction 
        self.obi_threshold = obi_threshold
        self.night_mode = night_mode
        
        # MICRO SIZE FORCE (AAVE FIX)
        # If size is too large on expensive assets (like AAVE $128), exchange might reject or leverage might overexpose.
        # Force size to be small and manageable.
        
        self.target_pos_size_usd = target_pos_size_usd # Respect argument
        self.target_profit_usd = target_profit_usd 
        self.logger = logging.getLogger("VolumeFarmer")
        
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        
        # ATOMIC OPTIMIZATION (ThreadPool)
        # "Clean everything that slows down the system"
        # Execute I/O (Requests) in separate threads to avoid blocking Event Loop.
        import concurrent.futures
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        # ATR / RISK MANAGER (Safety Check)
        self.risk_per_trade_usd = 2.0 # Max loss per trade allowed
        
        # EQUITY PROTECTION (Hard Stop)
        self.min_equity_threshold = 2.0 # Reduced to $2 to allow recovery operation
        
        self.is_running = False
        # State now needs to be dynamic or use defaultdict
        # We will initialize state on the fly in _process_symbol if needed
        self.state = {} 
        self.order_timers = {} # Track order age: {order_id: timestamp}
        
    def _check_risk(self, symbol):
        """Calculates risk based on ATR. Returns True if safe."""
        try:
            klines = self.data_client.get_klines(symbol, "15m", limit=20)
            if not klines: return True # Fallback
            
            # Manual calculation without Pandas for performance
            highs = [float(k['high']) for k in klines]
            lows = [float(k['low']) for k in klines]
            close = float(klines[-1]['close'])
            
            # Simple ATR Calculation (High - Low)
            tr_sum = sum((h - l) for h, l in zip(highs, lows))
            atr = tr_sum / len(klines)
            
            # Stop Loss Distance (3x ATR)
            sl_dist = atr * 3
            
            # Risk Amount
            risk_amt = (self.target_pos_size_usd / close) * sl_dist
            
            if risk_amt > self.risk_per_trade_usd:
                self.logger.warning(f"HIGH RISK: {symbol} (Risk: ${risk_amt:.2f} > Limit: ${self.risk_per_trade_usd}) - Reducing Size...")
                # Reduce size dynamically to fit risk
                # New Size = (Limit / Risk) * Current Size
                reduction_factor = self.risk_per_trade_usd / risk_amt
                self.target_pos_size_usd = self.target_pos_size_usd * reduction_factor
                self.logger.warning(f"Size Adjusted to: ${self.target_pos_size_usd:.2f}")
                
            return True
        except Exception as e:
            self.logger.error(f"Risk Check Error: {e}")
            return True

    async def start(self):
        # INITIAL EQUITY CHECK
        try:
            collateral = self.transport.get_futures_collateral()
            if collateral:
                equity = float(collateral.get('netEquity', 0))
                self.logger.info(f"INITIAL EQUITY: ${equity:.2f}")
                
                if equity < self.min_equity_threshold:
                    self.logger.error(f"CRITICAL EQUITY (${equity:.2f} < ${self.min_equity_threshold}). ABORTING FOR PROTECTION.")
                    return
                    
                # DYNAMIC SIZING (Max 15% of Equity per trade x Leverage)
                # Ex: $32 Equity * 0.15 = $4.8 Margin * 7x Lev = $33.6 Size
                safe_size = (equity * 0.15) * self.leverage
                
                # If safe size is smaller than target, adjust.
                # Allowing Micro Sizes for small accounts ($3)
                if safe_size < 3: safe_size = 3
                
                if self.target_pos_size_usd > safe_size:
                    self.logger.warning(f"Requested Size (${self.target_pos_size_usd}) > Safe Size (${safe_size:.2f}). Adjusting...")
                    self.target_pos_size_usd = safe_size
            else:
                self.logger.warning(f"Failed to read Futures Equity. Using default parameters with caution.")
                
        except Exception as e:
            self.logger.error(f"Error checking equity: {e}")

        self.logger.info(f"STARTING VOLUME FLEET: {self.active_symbols} | Lev {self.leverage}x")
        self.logger.info(f"   -> Mode: {self.mode.upper()} ({self.direction.upper()})")
        self.logger.info(f"   -> Pool: {len(self.candidate_pool)} assets | Slots: {self.max_slots}")
        
        self.is_running = True
        
        # Loop Speed Adjustment based on Slots/Turbo
        loop_speed = 0.01 if self.max_slots >= 5 else 0.1
        
        while self.is_running:
            try:
                tasks = []
                # Create copy to avoid modification during iteration if we were removing
                # But here we just launch tasks
                current_batch = list(self.active_symbols)
                
                for symbol in current_batch:
                    if symbol not in self.state:
                         self.state[symbol] = {
                             'last_price': 0, 
                             'active_id': None, 
                             'trailing_activated': False,
                             'position_start_time': None
                         }
                    tasks.append(self._process_symbol(symbol))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(loop_speed) # Dynamic Speed
                
            except Exception as e:
                self.logger.error(f"Erro no Loop Principal: {e}")
                await asyncio.sleep(5)

    def _rotate_symbol(self, old_symbol):
        """Remove old symbol and pick a new one from candidates"""
        self.logger.info(f"ROTATION: Removendo {old_symbol} (Stuck/Illiquid)...")
        
        if old_symbol in self.active_symbols:
            self.active_symbols.remove(old_symbol)
            
        # Clean state
        if old_symbol in self.state: del self.state[old_symbol]
        
        # Pick new
        available = [s for s in self.candidate_pool if s not in self.active_symbols and s != old_symbol]
        if available:
            new_symbol = random.choice(available)
            self.active_symbols.append(new_symbol)
            self.logger.info(f"ROTATION: Adicionado {new_symbol} ao Active Set.")
        else:
            self.logger.warning("ROTATION: Sem candidatos disponíveis para rotação.")
            # Add back old one if nothing else? Or just shrink?
            # Let's add back old one to keep slots full if no option
            self.active_symbols.append(old_symbol)

    async def _process_symbol(self, symbol):
        """Processa a lógica para um único ativo (NON-BLOCKING I/O)"""
        try:
            loop = asyncio.get_running_loop()
            import time
            
            # 0. Guard Ativo (Straddle e Surf)
            await self._guard_orders(symbol)
            
            # RISK PRE-CHECK (ONCE PER CYCLE)
