import os
import json
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

def check_balance():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print("\n CHECKING BALANCE & COLLATERAL...")
    print("===================================")
    
    # 1. Check Collateral (Futures)
    try:
        collat = data.get_account_collateral()
        print("\n COLLATERAL RESPONSE (Raw):")
        print(json.dumps(collat, indent=2))
        
        available = float(collat.get('availableToTrade', 0))
        balance = float(collat.get('balance', 0))
        margin_used = float(collat.get('initialMargin', 0))
        
        print(f"\n KEY METRICS:")
        print(f"   - Balance (Total): ${balance:.2f}")
        print(f"   - Initial Margin Used: ${margin_used:.2f}")
        print(f"   - Available to Trade: ${available:.2f}")
        
    except Exception as e:
        print(f"    Error checking collateral: {e}")

    # 2. Check Spot Balances (Just in case)
    try:
        spot = data.get_balances()
        print("\n SPOT BALANCES:")
        print(json.dumps(spot, indent=2))
    except Exception as e:
        print(f"    Error checking spot: {e}")

if __name__ == "__main__":
    check_balance()
