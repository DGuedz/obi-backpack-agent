import os
import sys
import json
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def check():
    load_dotenv()
    transport = BackpackTransport()
    print(" Checking Collateral Structure...")
    try:
        data = transport.get_account_collateral()
        print(f"Type: {type(data)}")
        print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict):
            print(f"NetEquity: {data.get('netEquity')}")
            print(f"Raw: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()