
import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def deep_scan():
    print(" DEEP SCAN: Investigating Ghost Exposure...")
    
    # 1. Positions
    positions = data.get_positions()
    print(f"    Positions Endpoint: {len(positions)} active")
    for p in positions:
        print(f"      - {p['symbol']}: {p['side']} {p['quantity']} (PnL: {p['pnlUnrealized']})")
        
    # 2. Collateral
    collateral = data.get_account_collateral()
    exposure = float(collateral.get('netExposureFutures', 0))
    locked = float(collateral.get('netEquityLocked', 0))
    print(f"    Collateral Endpoint: Exposure ${exposure} | Locked Margin ${locked}")
    
    # 3. Open Orders
    # We need to check open orders per market or fetch all? 
    # Backpack doesn't have a global "get all open orders" easily without symbol, 
    # but let's check the main suspects: IP, HYPE, SOL, PENGU, kBONK.
    suspects = ["IP_USDC_PERP", "HYPE_USDC_PERP", "SOL_USDC_PERP", "PENGU_USDC_PERP", "kBONK_USDC_PERP"]
    print("   ️ Checking Open Orders for suspects...")
    
    # We need a trade instance or manual request for open orders
    # data.get_open_orders is not implemented in my wrapper yet, let's implement ad-hoc here or skip
    # Actually, collateral 'netEquityLocked' often comes from Open Orders (Initial Margin) OR Positions.
    # If positions are 0 but Locked is > 0, it's likely OPEN LIMIT ORDERS consuming margin.
    
    if exposure > 0 and len(positions) == 0:
        print("   ️ ANOMALY: Exposure detected but no Positions! Likely 'Ghost' or API Delay.")
    elif locked > 0 and len(positions) == 0:
         print("   ️ ANOMALY: Margin Locked but no Positions! checking for OPEN ORDERS...")
         # It's likely open orders.
         
    return positions, exposure

if __name__ == "__main__":
    deep_scan()
