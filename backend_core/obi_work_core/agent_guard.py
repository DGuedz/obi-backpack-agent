import subprocess
import time
import sys
import os
import logging
from datetime import datetime, timedelta

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [OBI-GUARD] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

AGENT_SCRIPT = "agent_loop.py"
MAX_RESTARTS_PER_HOUR = 10
RESTART_WINDOW = 3600  # 1 hour in seconds
MIN_BACKOFF = 1
MAX_BACKOFF = 300  # 5 minutes

class AgentWatchdog:
    """
    OBI WORK - AGENT WATCHDOG (Process Supervisor)
    Ensures the agent loop stays alive, handles crashes gracefully, 
    and prevents crash loops via exponential backoff.
    """
    
    def __init__(self, target_script: str, args: list = None):
        self.target_script = target_script
        self.args = args or []
        self.restart_history = []
        self.consecutive_crashes = 0
        
    def _clean_history(self):
        """Remove restart timestamps older than the window."""
        now = time.time()
        self.restart_history = [t for t in self.restart_history if now - t < RESTART_WINDOW]

    def _should_backoff(self) -> float:
        """Calculate backoff time based on crash frequency."""
        self._clean_history()
        
        # Check frequency limit
        if len(self.restart_history) >= MAX_RESTARTS_PER_HOUR:
            logger.critical("Restart limit reached (CrashLoop detected). Supervisor pausing for 1 hour.")
            return 3600
        
        # Exponential backoff based on consecutive crashes
        if self.consecutive_crashes > 0:
            backoff = min(MIN_BACKOFF * (2 ** (self.consecutive_crashes - 1)), MAX_BACKOFF)
            return backoff
            
        return 0

    def run(self):
        logger.info(f"Starting Supervisor for {self.target_script}...")
        
        while True:
            # 1. Prepare Command
            cmd = [sys.executable, self.target_script] + self.args
            
            logger.info(f"Launching Agent (Attempt {len(self.restart_history) + 1})...")
            start_time = time.time()
            
            # 2. Execute
            try:
                process = subprocess.Popen(cmd)
                return_code = process.wait()
            except KeyboardInterrupt:
                logger.info("Supervisor stopped by user.")
                if process:
                    process.terminate()
                break
            except Exception as e:
                logger.error(f"Supervisor Error: {e}")
                return_code = -1

            # 3. Analyze Exit
            uptime = time.time() - start_time
            
            if return_code == 0:
                logger.info("Agent exited normally (0). Restarting immediately.")
                self.consecutive_crashes = 0 # Reset on clean exit
            else:
                logger.warning(f"Agent crashed with code {return_code}. Uptime: {uptime:.2f}s")
                
                # If uptime was decent (> 60s), reset consecutive crash counter
                if uptime > 60:
                    self.consecutive_crashes = 0
                else:
                    self.consecutive_crashes += 1

            # 4. Record Restart
            self.restart_history.append(time.time())
            
            # 5. Backoff Strategy
            wait_time = self._should_backoff()
            if wait_time > 0:
                logger.warning(f"Backing off for {wait_time}s...")
                time.sleep(wait_time)
            else:
                time.sleep(1) # Minimal delay

if __name__ == "__main__":
    # Pass arguments through to the agent
    # Example usage: python3 agent_guard.py --mode safe --max-workers 2
    script_args = sys.argv[1:]
    
    # Ensure we are in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    guard = AgentWatchdog(AGENT_SCRIPT, script_args)
    guard.run()
