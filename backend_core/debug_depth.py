
import requests
import json

def debug_depth():
    symbol = "SOL_USDC_PERP"
    url = f"https://api.backpack.exchange/api/v1/depth?symbol={symbol}"
    
    print(f" DEBUGGING DEPTH FOR {symbol}")
    print(f"URL: {url}")
    
    try:
        resp = requests.get(url)
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            # print("RAW DATA (Truncated):")
            # print(str(data)[:500])
            
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            print(f"\nBids Count: {len(bids)}")
            print(f"Asks Count: {len(asks)}")
            
            if bids and asks:
                best_bid = float(bids[0][0]) # Price is usually first element
                best_ask = float(asks[0][0])
                print(f"Best Bid: {best_bid}")
                print(f"Best Ask: {best_ask}")
                
                spread = (best_ask - best_bid) / best_bid
                print(f"Spread: {spread*100:.4f}%")
            else:
                print(" EMPTY BIDS/ASKS")
                
        else:
            print(f"Error Response: {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_depth()
