import os
import sys
import time
import asyncio
import logging
import subprocess
import signal
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), 'tools'))

from backpack_transport import BackpackTransport
from smart_money_scanner import SmartMoneyScanner

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [OBI BRAIN] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_brain.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AgentBrain")

class AutonomousAgent:
    def __init__(self):
        load_dotenv()
        self.transport = BackpackTransport()
        self.scanner = SmartMoneyScanner()
        self.active_process = None
        self.current_strategy = None
        self.min_equity = 2.0 # Global Hard Stop
        self.target_equity = 50.0 # Recovery Target
        
    def _check_equity(self):
        """Checks account health and stops everything if critical"""
        try:
            collateral = self.transport.get_futures_collateral()
            if not collateral: return 0
            
            equity = float(collateral.get('netEquity', 0))
            logger.info(f" Current Equity: ${equity:.2f}")
            
            if equity < self.min_equity:
                logger.error(f" CRITICAL EQUITY (${equity:.2f}). STOPPING ALL SYSTEMS.")
                self._kill_process()
                sys.exit(1)
                
            return equity
        except Exception as e:
            logger.error(f"Equity check error: {e}")
            return 0

    def _kill_process(self):
        if self.active_process:
            logger.info(" Killing active process...")
            self.active_process.send_signal(signal.SIGINT) # Try graceful stop
            time.sleep(2)
            if self.active_process.poll() is None:
                self.active_process.kill() # Brute force
            self.active_process = None
            self.current_strategy = None

    async def _decide_strategy(self):
        """The Brain: Analyzes market conditions and selects the best strategy"""
        logger.info(" Analyzing market for tactical decision...")
        
        # 1. Opportunity Scan (OBI & Walls)
        opportunities = await self.scanner.scan_market()
        if not opportunities:
            logger.warning("️ No clear opportunities detected. Waiting...")
            return None
            
        best_asset = opportunities[0]
        symbol = best_asset['symbol']
        obi = best_asset['obi']
        wall_strength = best_asset.get('wall_strength', 0)
        
        logger.info(f" Top Asset: {symbol} (OBI {obi:.2f} | Wall {wall_strength:.1f}x)")
        
        # 2. Strategy Selection
        cmd = []
        
        # Scenario A: High Volatility + Clear Direction (OBI > 0.35) -> OBI SNIPER
        if abs(obi) > 0.35:
            logger.info("️ MODE SELECTED: OBI SNIPER (High Precision)")
            cmd = [
                "python3", "tools/volume_farmer.py",
                "--symbols", symbol,
                "--leverage", "5", # Slight leverage increase for high conviction
                "--size", "10.0",  # Larger size
                "--profit", "0.25",
                "--turbo",
                "--obi_sniper", # VWAP Filter Flag
                "--surf"
            ]
            
        # Scenario B: Accumulation / Lateral (OBI < 0.2) -> SWING FARM
        else:
            logger.info(" MODE SELECTED: SWING FARM (Micro Lots)")
            # Pick top 3 for diversification
            top_3 = [o['symbol'] for o in opportunities[:3]]
            cmd = [
                "python3", "tools/volume_farmer.py",
                "--symbols", *top_3,
                "--leverage", "3",
                "--size", "3.0", # Micro size
                "--profit", "0.50", # Larger target
                "--surf"
            ]
            
        return cmd

    def run(self):
        logger.info(" AUTONOMOUS AGENT STARTED (OBI PROTOCOL)")
        
        while True:
            try:
                # 1. Health Check
                equity = self._check_equity()
                
                # 2. Monitor Active Process
                if self.active_process:
                    if self.active_process.poll() is not None:
                        logger.info("️ Child process died. Restarting cycle...")
                        self.active_process = None
                    else:
                        # Process healthy. Sleep and check again.
                        time.sleep(60) 
                        continue
                        
                # 3. Decision
                cmd = asyncio.run(self._decide_strategy())
                
                if cmd:
                    logger.info(f" Executing: {' '.join(cmd)}")
                    self.active_process = subprocess.Popen(cmd)
                    self.current_strategy = cmd
                    
                time.sleep(10) # Wait before loop
                
            except KeyboardInterrupt:
                logger.info(" Manual stop requested.")
                self._kill_process()
                break
            except Exception as e:
                logger.error(f" Critical Brain Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    brain = AutonomousAgent()
    brain.run()
