
import os
import sys
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def test_prediction_access():
    print(" OBI PREDICTION LINK TEST")
    transport = BackpackTransport()
    
    print("\n1. Fetching Active Predictions (/api/v1/prediction?resolved=false)...")
    try:
        markets = transport.get_prediction_markets()
        if markets:
            print(f"    SUCCESS! Found {len(markets)} active prediction markets.")
            for m in markets[:3]: # Show first 3
                print(f"      - Symbol: {m.get('symbol', 'Unknown')}")
                print(f"        Title: {m.get('title', 'No Title')}")
                print(f"        Expiry: {m.get('expiry', 'No Expiry')}")
                print(f"        Options: {m.get('outcomes', [])}")
        else:
            print("   ️  No active prediction markets found (Empty List).")
            
    except Exception as e:
        print(f"    Error fetching predictions: {e}")

if __name__ == "__main__":
    test_prediction_access()
