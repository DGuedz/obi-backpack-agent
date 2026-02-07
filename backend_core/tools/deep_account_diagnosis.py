
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def deep_diagnosis():
    print("️ DEEP ACCOUNT DIAGNOSIS: WHERE IS THE MONEY?")
    print("="*60)
    load_dotenv()
    transport = BackpackTransport()
    
    # 1. CAPITAL / BALANCES
    print("\n 1. CAPITAL ANALYSIS (/api/v1/capital)")
    try:
        capital = transport._send_request("GET", "/api/v1/capital", "balanceQuery")
        # Filter only non-zero
        if isinstance(capital, dict):
            non_zero = {k:v for k,v in capital.items() if float(v.get('available','0')) > 0 or float(v.get('locked','0')) > 0 or float(v.get('staked','0')) > 0}
            print(f"    Non-Zero Balances: {json.dumps(non_zero, indent=2)}")
        else:
            print(f"    Raw Capital: {capital}")
    except Exception as e:
        print(f"    Error: {e}")

    # 2. FUTURES COLLATERAL
    print("\n 2. FUTURES COLLATERAL (/api/v1/capital/collateral)")
    try:
        collateral = transport._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
        print(f"    Collateral Info: {json.dumps(collateral, indent=2)}")
    except Exception as e:
        print(f"    Error: {e}")

    # 3. LENDING POSITIONS
    print("\n 3. LENDING POSITIONS (/api/v1/borrowLend/positions)")
    try:
        lending = transport._send_request("GET", "/api/v1/borrowLend/positions", "borrowLendPositionQuery")
        print(f"    Lending Positions: {json.dumps(lending, indent=2)}")
    except Exception as e:
        print(f"    Error: {e}")

    # 4. DEPOSIT HISTORY (Last 10)
    print("\n 4. DEPOSIT HISTORY (/wapi/v1/history/deposits)")
    try:
        # Note: Usually wapi for history
        # Endpoint might vary, checking standard Backpack patterns or openapi
        # OpenApi says nothing about deposit history in public paths? 
        # Let's try /wapi/v1/history/deposits with instruction depositHistoryQueryAll
        params = {"limit": "10", "offset": "0"}
        deposits = transport._send_request("GET", "/wapi/v1/history/deposits", "depositHistoryQueryAll", params)
        print(f"    Recent Deposits: {json.dumps(deposits, indent=2)}")
    except Exception as e:
        print(f"    Error (Deposits): {e}")

    # 5. WITHDRAWAL HISTORY (Last 10)
    print("\nout 5. WITHDRAWAL HISTORY (/wapi/v1/history/withdrawals)")
    try:
        params = {"limit": "10", "offset": "0"}
        withdrawals = transport._send_request("GET", "/wapi/v1/history/withdrawals", "withdrawalHistoryQueryAll", params)
        print(f"    Recent Withdrawals: {json.dumps(withdrawals, indent=2)}")
    except Exception as e:
        print(f"    Error (Withdrawals): {e}")

if __name__ == "__main__":
    deep_diagnosis()
