import time
import base64
import requests
import json
import sys
from cryptography.hazmat.primitives.asymmetric import ed25519

# Test Candidates
KEYS_TO_TEST = [
    {
        "name": "NEW_KEY (OBI01)",
        "api_key": "WLI6r7Pwajizorz7bdWhoNiG9Irbt66BaYRlOzOBcPc=",
        "api_secret": "IUQA6AhSgWPgTtLCMY6BUl1qSVg4Cl7lNppJ+srmFRA="
    },
    {
        "name": "OLD_KEY (Found in comments)",
        "api_key": "ZZ67XROtu4ccE+ihBPK2pDjui64L3HGGIpQMqMgrdwI=",
        "api_secret": "iab+s94mwXSz0TucSVxYUUCWfw0a9yaCMcs61yPwSJw="
    }
]

BASE_URL = "https://api.backpack.exchange"

class BackpackAuth:
    def __init__(self, api_key_base64, private_key_base64):
        self.api_key = api_key_base64
        try:
            self.private_key_bytes = base64.b64decode(private_key_base64)
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(self.private_key_bytes)
        except Exception as e:
            print(f" Error decoding key {api_key_base64[:10]}...: {e}")
            self.private_key = None

    def get_headers(self, instruction=None, params=None):
        if not self.private_key:
            return {}
            
        if params is None:
            params = {}
        
        timestamp = int(time.time() * 1000)
        window = 5000
        
        sorted_keys = sorted(params.keys())
        query_string_parts = []
        for key in sorted_keys:
            value = params[key]
            if isinstance(value, bool):
                value = str(value).lower()
            query_string_parts.append(f"{key}={value}")
            
        param_string = "&".join(query_string_parts)
        
        if instruction:
            if param_string:
                signature_payload = f"instruction={instruction}&{param_string}"
            else:
                signature_payload = f"instruction={instruction}"
        else:
            signature_payload = param_string
            
        if signature_payload:
            signature_payload += f"&timestamp={timestamp}&window={window}"
        else:
            signature_payload = f"timestamp={timestamp}&window={window}"
            
        signature_bytes = self.private_key.sign(signature_payload.encode('utf-8'))
        signature_base64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        headers = {
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "X-API-Key": self.api_key,
            "X-Signature": signature_base64,
            "Content-Type": "application/json; charset=utf-8"
        }
        
        return headers

def check_balance(key_data):
    print(f"\n Testing {key_data['name']}...")
    
    auth = BackpackAuth(key_data['api_key'], key_data['api_secret'])
    if not auth.private_key:
        print("    Invalid Private Key format.")
        return

    # 1. Check Futures Balance (/api/v1/capital)
    print("    Checking Futures Balance...")
    headers_cap = auth.get_headers("balanceQuery", {}) # Changed from capitalQuery to balanceQuery
    try:
        response = requests.get(BASE_URL + "/api/v1/capital", headers=headers_cap, timeout=10)
        print(f"      [DEBUG] Capital Response: {response.text[:200]}") # Print raw response
        if response.status_code == 200:
            capital_data = response.json()
            if isinstance(capital_data, dict) and 'USDC' in capital_data:
                print(f"      Futures USDC: {capital_data['USDC'].get('availableToTrade', 0)}")
            else:
                print(f"      Futures USDC: 0 (No USDC key or not dict)")
        else:
            print(f"       Futures Error: {response.status_code}")
    except Exception as e:
        print(f"       Exception: {e}")

    # 2. Check Spot Balance (/api/v1/assets)
    print("    Checking Spot Balance...")
    headers_assets = auth.get_headers("assetsQuery", {})
    try:
        response = requests.get(BASE_URL + "/api/v1/assets", headers=headers_assets, timeout=10)
        print(f"      [DEBUG] Assets Response: {response.text[:200]}") # Print raw response
        if response.status_code == 200:
            data = response.json()
            # Normalize data to list of dicts if it's a dict
            items_to_check = []
            if isinstance(data, dict):
                for symbol, details in data.items():
                    if isinstance(details, dict):
                        d = details.copy()
                        d['symbol'] = symbol
                        items_to_check.append(d)
            elif isinstance(data, list):
                items_to_check = data
                
            print(f"      Non-zero Spot Assets (Count: {len(items_to_check)}):")
            found_any = False
            for asset in items_to_check:
                symbol = asset.get('symbol')
                available = float(asset.get('available', 0))
                locked = float(asset.get('locked', 0))
                staked = float(asset.get('staked', 0))
                total = available + locked + staked
                
                if total > 0:
                    print(f"      - {symbol}: {total} (Avail: {available})")
                    found_any = True
            
            if not found_any:
                print("      (No assets found with balance > 0)")
        else:
            print(f"       Spot Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"       Exception: {e}")

    # 3. Check Order History (More reliable than fills sometimes)
    print("    Checking Order History (Last 5)...")
    headers_hist = auth.get_headers("orderHistoryQueryAll", {}) 
    try:
        # Try /api/v1/history/orders
        response = requests.get(BASE_URL + "/api/v1/history/orders", headers=headers_hist, timeout=10)
        if response.status_code == 200:
            orders = response.json()
            print(f"      Orders Found: {len(orders)}")
            for i, order in enumerate(orders[:5]):
                print(f"      [{i}] {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ {order.get('price')} ({order.get('status')})")
        else:
            print(f"       Order History Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"       Exception: {e}")

    # 4. Check Account Identity (Who am I?)
    print("    Checking Account Identity...")
    headers_acc = auth.get_headers("accountQuery", {})
    try:
        response = requests.get(BASE_URL + "/api/v1/account", headers=headers_acc, timeout=10)
        print(f"      [DEBUG] Account Response: {response.text[:200]}") # Print raw response
        if response.status_code == 200:
            info = response.json()
            print(f"      Account Name: {info.get('name')}")
            print(f"      Tier: {info.get('tier')}")
            print(f"      Subaccount ID: {info.get('subaccountId')}") # Hypothetical field
        else:
            print(f"       Account Info Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"       Exception: {e}")

    # 5. Check Deposit Address (Identity Verification)
    print("    Checking Deposit Address (Identity Check)...")
    headers_dep = auth.get_headers("depositAddressQuery", {"blockchain": "Solana"})
    try:
        # GET /api/v1/capital/deposit/address?blockchain=Solana
        url = BASE_URL + "/api/v1/capital/deposit/address?blockchain=Solana"
        response = requests.get(url, headers=headers_dep, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"      Deposit Address: {data.get('address')}")
        else:
            print(f"       Deposit Addr Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"       Exception: {e}")

if __name__ == "__main__":
    print(" DIAGNOSTIC: Testing API Keys for Balance Access")
    for key in KEYS_TO_TEST:
        check_balance(key)
