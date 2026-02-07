
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def inspect_prediction_structure():
    print(" OBI PREDICTION DEEP INSPECTION")
    transport = BackpackTransport()
    
    try:
        markets = transport.get_prediction_markets()
        if markets:
            print(f"    FOUND {len(markets)} MARKETS. Dumping first 3 raw JSONs for analysis:\n")
            
            for i, m in enumerate(markets[:3]):
                print(f"--- MARKET #{i+1} ---")
                print(json.dumps(m, indent=4))
                print("-------------------")
        else:
            print("   ️  No active prediction markets found.")
            
    except Exception as e:
        print(f"    Error: {e}")

if __name__ == "__main__":
    inspect_prediction_structure()
