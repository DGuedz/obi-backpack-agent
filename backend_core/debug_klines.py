
import requests
import json
import time

def debug_klines():
    symbol = "SOL_USDC_PERP"
    interval = "1h"
    limit = 60
    # Calculate start time for 60 candles of 1h
    # 1h = 3600s
    end_ts = int(time.time())
    start_ts = end_ts - (limit * 3600)
    
    # Try adding startTime
    url = f"https://api.backpack.exchange/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}&startTime={start_ts}"
    
    print(f" DEBUGGING KLINES FOR {symbol}")
    print(f"URL: {url}")
    
    try:
        start_time = time.time()
        resp = requests.get(url)
        end_time = time.time()
        
        print(f"Status Code: {resp.status_code}")
        print(f"Latency: {end_time - start_time:.4f}s")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Klines Count: {len(data)}")
            if len(data) > 0:
                print("First Kline:", data[0])
                print("Last Kline:", data[-1])
        else:
            print(f"Error Response: {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_klines()
