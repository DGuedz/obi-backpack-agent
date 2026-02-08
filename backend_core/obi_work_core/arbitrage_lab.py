import time
import sys
import os
import uuid

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

class ArbitrageLab:
    """
    OBI WORK - ARBITRAGE LAB
    Modality: Arbitrator
    Strategy: Basis Arbitrage (Spot vs Perp)
    """
    
    def __init__(self):
        self.client = BackpackClient()
        self.session_id = str(uuid.uuid4())[:8]
        
    def run_scan(self):
        print(f"\n⚖️ ARBITRAGE LAB (Session: {self.session_id})")
        print("Strategy: Spot-Perp Basis Monitor (SOL)")
        print("=" * 50)
        
        # 1. Fetch Spot Price
        print("1. Fetching SPOT Price (SOL_USDC)...")
        spot_ticker = self.client.get_ticker("SOL_USDC")
        spot_price = float(spot_ticker.get('lastPrice', 0))
        
        # 2. Fetch Perp Price
        print("2. Fetching PERP Price (SOL_USDC_PERP)...")
        perp_ticker = self.client.get_ticker("SOL_USDC_PERP")
        perp_price = float(perp_ticker.get('lastPrice', 0))
        
        if spot_price == 0 or perp_price == 0:
            print("❌ Failed to fetch prices.")
            return
            
        print(f"   SPOT: ${spot_price:.2f}")
        print(f"   PERP: ${perp_price:.2f}")
        
        # 3. Calculate Basis
        diff = perp_price - spot_price
        basis_pct = (diff / spot_price) * 100
        
        print(f"\n📊 ANALYSIS:")
        print(f"   Difference: ${diff:.4f}")
        print(f"   Basis:      {basis_pct:.4f}%")
        
        # 4. Strategy Check
        if basis_pct > 0.1:
            print("\n🚀 OPPORTUNITY: POSITIVE BASIS (Contango)")
            print("   Action: Buy SPOT + Sell PERP (Funding Rate Farming)")
        elif basis_pct < -0.1:
            print("\n🚀 OPPORTUNITY: NEGATIVE BASIS (Backwardation)")
            print("   Action: Sell SPOT + Buy PERP")
        else:
            print("\nzzz Market Efficient (Basis < 0.1%)")
            
        # Funding Rate (Optional fetch if available in ticker or instrument)
        # Assuming we might want to see funding rate for Arb context.
        
        print("\n✅ Arbitrage Scan Complete.")

if __name__ == "__main__":
    lab = ArbitrageLab()
    lab.run_scan()
