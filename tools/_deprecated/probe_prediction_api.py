
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def probe():
    transport = BackpackTransport()
    
    print("️ PROBING PREDICTION MARKETS...")

    # 1. Check Public Markets
    print("\n1. Checking Public /api/v1/markets...")
    markets = transport.get_all_markets()
    prediction_markets = [m for m in markets if 'prediction' in str(m).lower() or 'up' in m.get('symbol', '').lower()]
    print(f"   Found {len(markets)} markets.")
    if prediction_markets:
        print(f"   Potential Prediction Markets: {[m['symbol'] for m in prediction_markets]}")
    else:
        print("   No obvious prediction markets found in public list.")

    # 2. Probe /wapi/v1/prediction/markets (Public/Private?)
    endpoints = [
        "/wapi/v1/prediction/markets",
        "/api/v1/prediction/markets",
        "/api/v1/predictions",
        "/wapi/v1/predictions",
        "/api/v1/prediction/events",
        "/wapi/v1/prediction/events"
    ]
    
    for ep in endpoints:
        print(f"\n2. Probing {ep} (GET)...")
        # Try without auth first
        url = f"https://api.backpack.exchange{ep}"
        try:
            resp = requests.get(url, timeout=3)
            print(f"   [No Auth] Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"    SUCCESS! Payload: {str(resp.json())[:100]}...")
            elif resp.status_code == 401:
                print("    401 Unauthorized (Auth needed)")
                # Try with Auth (Guessing Instruction)
                instructions = ["predictionQuery", "marketQuery", "predictionQueryAll", "query"]
                for instr in instructions:
                    print(f"      Trying auth with instruction: {instr}")
                    res = transport._send_request("GET", ep, instr)
                    if res:
                        print(f"       AUTH SUCCESS with {instr}!")
                        print(f"      Payload: {str(res)[:100]}...")
                        break
            else:
                print(f"    Status: {resp.status_code}")
        except Exception as e:
            print(f"   ️ Error: {e}")

if __name__ == "__main__":
    probe()
