
import os
import sys
import json
from dotenv import load_dotenv

# Add Legacy Path for Dependencies
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
import requests

load_dotenv()

def debug_balance():
    print(" DEBUGGING BALANCE...")
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    base_url = "https://api.backpack.exchange"
    
    # 1. Check Capital (Spot/General)
    print("\n--- /api/v1/capital ---")
    headers = auth.get_headers(instruction="balanceQuery")
    try:
        resp = requests.get(f"{base_url}/api/v1/capital", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Raw: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Check Collateral (Futures)
    print("\n--- /api/v1/capital/collateral ---")
    headers = auth.get_headers(instruction="collateralQuery")
    try:
        resp = requests.get(f"{base_url}/api/v1/capital/collateral", headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Raw: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_balance()
