import os
import requests
import json
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

def audit_spot_positions():
    print("\n️‍️ [SPOT AUDIT] Scanning for Phantom Assets...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    try:
        # Get Spot Balances
        balances = data.get_balances()
        # Structure: {'USDC': {'available': 100, 'locked': 0}, 'BTC': ...}
        
        found_phantom = False
        
        for asset, bal in balances.items():
            available = float(bal.get('available', 0))
            locked = float(bal.get('locked', 0))
            total = available + locked
            
            # Ignore USDC (Collateral) and Small Dust
            if asset == 'USDC' or total < 0.0001: 
                continue
                
            print(f"   ️ FOUND SPOT ASSET: {total} {asset} (Locked: {locked})")
            found_phantom = True
            
            # Recommendation
            val_usdc = 0 # Need ticker to know value
            print(f"      -> Action Required: SELL {asset} to convert to USDC Collateral.")
            
            # Auto-Liquidation?
            # Dangerous if user holds long term spot.
            # Just report for now.
            
        if not found_phantom:
            print("    No Phantom Spot Assets found. Clean.")
            
    except Exception as e:
        print(f"    Audit Error: {e}")

if __name__ == "__main__":
    audit_spot_positions()
