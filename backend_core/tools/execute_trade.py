import os
import sys
import time
import json
import base64
import requests
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

API_KEY = os.getenv("BACKPACK_API_KEY")
API_SECRET = os.getenv("BACKPACK_API_SECRET")

try:
    from nacl.signing import SigningKey
except ImportError:
    print("Erro: Biblioteca 'pynacl' necessaria.")
    exit(1)

class BackpackExecutionClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = base64.b64decode(api_secret)
        self.base_url = "https://api.backpack.exchange"

    def _sign(self, instruction, params, timestamp, window=5000):
        param_str = ""
        if params:
            sorted_keys = sorted(params.keys())
            param_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        
        message = f"instruction={instruction}"
        if param_str:
            message += f"&{param_str}"
        message += f"&timestamp={timestamp}&window={window}"
        
        signing_key = SigningKey(self.api_secret)
        signed = signing_key.sign(message.encode('utf-8'))
        return base64.b64encode(signed.signature).decode('utf-8')

    def _headers(self, instruction, params={}):
        timestamp = int(time.time() * 1000)
        window = 5000
        signature = self._sign(instruction, params, timestamp, window)
        return {
            "X-API-Key": self.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json"
        }

    def execute_order(self, symbol, side, quantity, price=None):
        url = f"{self.base_url}/api/v1/order"
        instruction = "orderExecute"
        
        params = {
            "symbol": symbol,
            "side": side, # "Bid" (Buy) or "Ask" (Sell)
            "orderType": "Market" if not price else "Limit",
            "quantity": str(quantity)
        }
        if price:
            params["price"] = str(price)
            
        headers = self._headers(instruction, params)
        try:
            print(f"Enviando ordem: {side} {quantity} {symbol}...")
            r = requests.post(url, json=params, headers=headers)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Erro Execução ({r.status_code}): {r.text}")
                return None
        except Exception as e:
            print(f"Erro ao executar ordem: {e}")
            return None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python execute_trade.py <SYMBOL> <SIDE:Bid/Ask> <QTY>")
        sys.exit(1)
        
    symbol = sys.argv[1]
    side = sys.argv[2]
    qty = sys.argv[3]
    
    if not API_KEY or not API_SECRET:
        print("Erro: API Keys não configuradas.")
        sys.exit(1)
        
    client = BackpackExecutionClient(API_KEY, API_SECRET)
    res = client.execute_order(symbol, side, qty)
    if res:
        print("SUCESSO!")
        print(json.dumps(res, indent=2))
