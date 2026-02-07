
import requests
import json

def check_sorting():
    symbol = "SOL_USDC_PERP"
    url = f"https://api.backpack.exchange/api/v1/depth?symbol={symbol}"
    
    print(f" CHECKING DEPTH SORTING FOR {symbol}")
    
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            print(f"Bids Count: {len(bids)}")
            if len(bids) > 0:
                print("First 3 Bids (Index 0, 1, 2):")
                for i in range(min(3, len(bids))):
                    print(f"  [{i}]: {bids[i]}")
                
                print("Last 3 Bids (Index -3, -2, -1):")
                for i in range(min(3, len(bids))):
                    print(f"  [{-3+i}]: {bids[-3+i]}")
            
            print(f"Asks Count: {len(asks)}")
            if len(asks) > 0:
                print("First 3 Asks (Index 0, 1, 2):")
                for i in range(min(3, len(asks))):
                    print(f"  [{i}]: {asks[i]}")
                    
                print("Last 3 Asks (Index -3, -2, -1):")
                for i in range(min(3, len(asks))):
                    print(f"  [{-3+i}]: {asks[-3+i]}")

        else:
            print(f"Error: {resp.status_code}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_sorting()
