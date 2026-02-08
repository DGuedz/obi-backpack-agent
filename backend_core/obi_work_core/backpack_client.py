import os
import time
import base64
import requests
import json
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class BackpackClient:
    """
    OBI WORK CORE - Backpack Exchange Client
    Standalone implementation for Core V4.0.
    """
    
    BASE_URL = "https://api.backpack.exchange"
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.api_secret = os.getenv('BACKPACK_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            print("WARNING: BACKPACK_API_KEY or BACKPACK_API_SECRET not found in env.")
            # We don't raise error here to allow dry-run/simulations if needed, 
            # but execution will fail.
            self.private_key = None
        else:
            self._init_keys()
            
    def _init_keys(self):
        try:
            # Handle padding
            padding = len(self.api_secret) % 4
            if padding > 0:
                self.api_secret += "=" * (4 - padding)
                
            private_bytes = base64.b64decode(self.api_secret)
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
        except Exception as e:
            print(f"CRITICAL: Failed to initialize keys: {e}")
            self.private_key = None

    def _get_headers(self, instruction: str = None, params: dict = None) -> dict:
        if not self.private_key:
            return {}
            
        timestamp = int(time.time() * 1000)
        window = 5000
        
        params_to_sign = params.copy() if params else {}
        params_to_sign['timestamp'] = str(timestamp)
        params_to_sign['window'] = str(window)
        
        # Sort and build string
        sorted_keys = sorted(params_to_sign.keys())
        query_parts = []
        for key in sorted_keys:
            val = params_to_sign[key]
            if isinstance(val, bool):
                val = str(val).lower()
            query_parts.append(f"{key}={val}")
            
        param_string = "&".join(query_parts)
        
        if instruction:
            sig_payload = f"instruction={instruction}&{param_string}" if param_string else f"instruction={instruction}"
        else:
            sig_payload = param_string or ""
            
        signature = self.private_key.sign(sig_payload.encode())
        signature_b64 = base64.b64encode(signature).decode()
        
        return {
            "X-API-Key": self.api_key,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8"
        }

    def get_balances(self) -> dict:
        endpoint = "/api/v1/capital"
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers("balanceQuery")
        
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                # Returns: {"SOL": {"available": "1.2", "locked": "0.0", "staked": "0.0"}, ...}
                return resp.json()
            else:
                print(f"API Error (Balances): {resp.text}")
                return {}
        except Exception as e:
            print(f"Network Error (Balances): {e}")
            return {}

    def get_futures_collateral(self) -> dict:
        endpoint = "/api/v1/capital/collateral"
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers("collateralQuery")
        
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API Error (Futures): {resp.text}")
                return {}
        except Exception as e:
            print(f"Network Error (Futures): {e}")
            return {}

    def get_candles(self, symbol: str, interval: str, limit: int = 100) -> list:
        endpoint = "/api/v1/klines"
        url = f"{self.BASE_URL}{endpoint}"
        
        # NOTE: Backpack API can be picky about startTime if not provided
        # Let's provide it to be safe (now - limit * interval)
        seconds_map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "4h": 14400, "1d": 86400
        }
        secs = seconds_map.get(interval, 300)
        end_ts = int(time.time())
        start_ts = end_ts - (limit * secs)
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
            # "startTime": start_ts # Removed to fix 'integer_int64' error if passed as string/float? 
            # The error says: failed to parse parameter `startTime`: Type "integer_int64" expects an input value.
            # This implies startTime might be required by the server even if docs say optional?
            # Or my previous impl didn't send it and it complained?
            # Wait, the logs showed: "failed to parse parameter `startTime`: Type "integer_int64" expects an input value."
            # My code DID NOT include startTime in params. So it seems REQUIRED?
        }
        # Let's add startTime as int
        params["startTime"] = int(start_ts)
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API Error (Candles): {resp.text}")
                return []
        except Exception as e:
            print(f"Network Error: {e}")
            return []

    def get_ticker(self, symbol: str) -> dict:
        endpoint = "/api/v1/ticker"
        url = f"{self.BASE_URL}{endpoint}"
        params = {"symbol": symbol}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                # Expected format: { "symbol": "SOL_USDC", "lastPrice": "150.00", "high24h": ..., "low24h": ..., "volume24h": ..., "bestBid": "149.95", "bestAsk": "150.05" }
                # Ensure bestBid/bestAsk are present or fallback
                data = resp.json()
                if 'bestBid' not in data:
                    # Fallback to lastPrice if bid/ask missing (rare)
                    data['bestBid'] = data.get('lastPrice', 0)
                if 'bestAsk' not in data:
                    data['bestAsk'] = data.get('lastPrice', 0)
                return data
            return {}
        except Exception as e:
            print(f"Network Error (Ticker): {e}")
            return {}

    def get_positions(self) -> list:
        endpoint = "/api/v1/position"
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers("positionQuery")
        
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API Error (Positions): {resp.text}")
                return []
        except Exception as e:
            print(f"Network Error (Positions): {e}")
            return []

    def get_open_orders(self, symbol: str = None) -> list:
        endpoint = "/api/v1/orders"
        url = f"{self.BASE_URL}{endpoint}"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        headers = self._get_headers("orderQuery", params)
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API Error (Open Orders): {resp.text}")
                return []
        except Exception as e:
            print(f"Network Error (Open Orders): {e}")
            return []

    def cancel_open_orders(self, symbol: str = None) -> list:
        endpoint = "/api/v1/orders"
        url = f"{self.BASE_URL}{endpoint}"
        params = {}
        if symbol:
            params["symbol"] = symbol
            
        headers = self._get_headers("orderCancelAll", params)
        
        try:
            # CHANGE: Use params (query string) instead of json body for DELETE
            resp = requests.delete(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API Error (Cancel All): {resp.text}")
                return []
        except Exception as e:
            print(f"Network Error (Cancel All): {e}")
            return []

    def execute_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None):
        endpoint = "/api/v1/order"
        url = f"{self.BASE_URL}{endpoint}"
        
        payload = {
            "symbol": symbol,
            "side": side, # Buy/Sell
            "orderType": order_type, # Limit/Market
            "quantity": str(quantity)
        }
        
        if price and order_type.upper() != "MARKET":
            payload["price"] = str(price)
            
        headers = self._get_headers("orderExecute", payload)
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"ORDER FAILED: {resp.text}")
                return None
        except Exception as e:
            print(f"Order Exception: {e}")
            return None

if __name__ == "__main__":
    client = BackpackClient()
    print("Testing Backpack Client...")
    ticker = client.get_ticker("SOL_USDC")
    print(f"SOL Price: {ticker.get('lastPrice')}")
