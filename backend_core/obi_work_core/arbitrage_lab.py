import time
import sys
import os
import uuid
from datetime import datetime

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

class ArbitrageLab:
    """
    OBI WORK - ARBITRAGE LAB (VSC COMPLIANT)
    Modality: Arbitrator
    Strategy: Basis Arbitrage (Spot vs Perp)
    Output: VSC Standard (Value-Separated Content)
    """
    
    def __init__(self):
        self.client = BackpackClient()
        self.session_id = str(uuid.uuid4())[:8]
        self.assets = ["SOL", "BTC", "ETH"]
        
    def get_basis(self, symbol):
        """
        Calculates Basis Spread for a given asset.
        Returns: dict or None
        """
        try:
            # 1. Fetch Spot
            spot_symbol = f"{symbol}_USDC"
            spot_ticker = self.client.get_ticker(spot_symbol)
            spot_price = float(spot_ticker.get('lastPrice', 0))
            
            # 2. Fetch Perp
            perp_symbol = f"{symbol}_USDC_PERP"
            perp_ticker = self.client.get_ticker(perp_symbol)
            perp_price = float(perp_ticker.get('lastPrice', 0))
            
            if spot_price == 0 or perp_price == 0:
                return None
                
            # 3. Calculate Metrics
            diff = perp_price - spot_price
            basis_pct = (diff / spot_price) * 100
            
            # Annualized (Theoretical, assuming basis persists/closes over 1 day * 365? 
            # Usually basis is just spread. Let's just track raw spread.)
            
            return {
                "symbol": symbol,
                "spot": spot_price,
                "perp": perp_price,
                "basis_pct": basis_pct,
                "diff": diff
            }
        except Exception as e:
            # Silent fail for VSC stream continuity
            return None

    def run_sentinel(self):
        """
        Continuous Monitoring Loop (Sentinel)
        """
        print(f"VSC_STREAM_START|SESSION_{self.session_id}|ARBITRAGE_LAB", flush=True)
        print("TIMESTAMP|ASSET|SPOT_PRICE|PERP_PRICE|BASIS_PCT|SPREAD_USD|SIGNAL", flush=True)
        
        while True:
            try:
                for asset in self.assets:
                    data = self.get_basis(asset)
                    
                    if data:
                        timestamp = datetime.utcnow().strftime("%H:%M:%S")
                        basis = data['basis_pct']
                        
                        # Generate Signal
                        signal = "NEUTRAL"
                        if basis > 0.15:
                            signal = "CONTANGO_ENTRY" # Buy Spot, Sell Perp
                        elif basis < -0.15:
                            signal = "BACKWARDATION_ENTRY" # Sell Spot, Buy Perp
                            
                        # VSC Output Line
                        log_line = (
                            f"{timestamp}|{data['symbol']}|{data['spot']:.2f}|"
                            f"{data['perp']:.2f}|{basis:.4f}%|${data['diff']:.4f}|{signal}"
                        )
                        print(log_line, flush=True)
                        
                    time.sleep(1) # Rate limit protection
                
                print("---", flush=True) # Visual separator for human observers (ignored by parser)
                time.sleep(5) # Scan interval
                
            except KeyboardInterrupt:
                print("VSC_STREAM_END|USER_ABORT", flush=True)
                break
            except Exception as e:
                print(f"ERROR|{str(e)}", flush=True)
                time.sleep(5)

if __name__ == "__main__":
    lab = ArbitrageLab()
    lab.run_sentinel()
