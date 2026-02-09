import os
import time
import base64
import requests
import sys
from dotenv import load_dotenv

# Force loading .env from root
# backend_core/tools/debug_keys.py -> ../../.env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

print(f"Loading .env from: {env_path}")

API_KEY = os.getenv("BACKPACK_API_KEY")
API_SECRET = os.getenv("BACKPACK_API_SECRET")

try:
    from nacl.signing import SigningKey
except ImportError:
    print("Error: 'pynacl' library required.")
    exit(1)

def debug_keys():
    if not API_KEY:
        print("[ERROR] BACKPACK_API_KEY not found in environment.")
        return
    if not API_SECRET:
        print("[ERROR] BACKPACK_API_SECRET not found in environment.")
        return

    print(f"API KEY (Prefix): {API_KEY[:4]}***REDACTED***")
    print(f"API SECRET (Prefix): {API_SECRET[:4]}***REDACTED***")
    
    # Test Authentication (Balance Query)
    base_url = "https://api.backpack.exchange"
    instruction = "balanceQuery"
    timestamp = int(time.time() * 1000)
    window = 5000
    
    # Signature
    params = {}
    param_str = ""
    message = f"instruction={instruction}&timestamp={timestamp}&window={window}"
    
    try:
        secret_decoded = base64.b64decode(API_SECRET)
        signing_key = SigningKey(secret_decoded)
        signed = signing_key.sign(message.encode('utf-8'))
        signature = base64.b64encode(signed.signature).decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Signing failed: {e}")
        return

    headers = {
        "X-API-Key": API_KEY,
        "X-Signature": signature,
        "X-Timestamp": str(timestamp),
        "X-Window": str(window),
        "Content-Type": "application/json"
    }
    
    print("\nSending Request to /api/v1/capital...")
    try:
        r = requests.get(f"{base_url}/api/v1/capital", headers=headers)
        print(f"Status Code: {r.status_code}")
        print(f"Response Body: {r.text}")
        
        if r.status_code == 200:
            print("\n[SUCCESS] Keys valid and authenticated!")
            data = r.json()
            if 'USDC' in data:
                print(f"USDC Balance: {data['USDC']['available']}")
            else:
                print("USDC Balance not found in response.")
        else:
            print("\n[FAILURE] Authentication or permission error.")
            
    except Exception as e:
        print(f"[ERROR] HTTP Request failed: {e}")

if __name__ == "__main__":
    debug_keys()
