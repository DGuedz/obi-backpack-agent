
import requests
import json

def debug_ticker():
    symbol = "SOL_USDC_PERP"
    url = f"https://api.backpack.exchange/api/v1/ticker?symbol={symbol}"
    
    print(f" DEBUGGING TICKER FOR {symbol}")
    print(f"URL: {url}")
    
    try:
        resp = requests.get(url)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("RAW DATA:")
            print(json.dumps(data, indent=2))
            
            # Check fields expected by Gatekeeper
            print("\nGATEKEEPER CHECKS:")
            print(f"bestBid: {data.get('bestBid')}")
            print(f"bestAsk: {data.get('bestAsk')}")
            print(f"quoteVolume: {data.get('quoteVolume')}")
        else:
            print(f"Error Response: {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_ticker()
