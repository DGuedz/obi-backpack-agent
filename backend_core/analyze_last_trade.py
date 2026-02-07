import sys
import os
import json
import time
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

symbol = "SOL_USDC_PERP"

print(f"--- ANALISANDO ÚLTIMOS TRADES DE {symbol} ---")

# 1. Verificar Posições Abertas
print("--- POSIÇÕES ATUAIS ---")
positions = data.get_positions()
print(json.dumps(positions, indent=2))

# 2. Verificar Ordens Abertas
print("\n--- ORDENS ABERTAS ---")
open_orders = data.get_open_orders(symbol)
print(json.dumps(open_orders, indent=2))

import requests

# 3. Tentar buscar histórico de ordens (All Orders)
# Endpoint: /api/v1/orders?symbol=SOL_USDC_PERP&limit=10
# Instrução: orderQueryAll
def get_order_history(symbol):
    url = "https://api.backpack.exchange/api/v1/orders"
    params = {'symbol': symbol, 'limit': 10} # Tentar trazer as últimas
    headers = auth.get_headers('orderQueryAll', params)
    res = requests.get(url, headers=headers, params=params)
    if res.status_code == 200:
        return res.json()
    else:
        print("Erro order history:", res.text)
        return []

print("\n--- HISTÓRICO DE ORDENS (ÚLTIMAS 10) ---")
history = get_order_history(symbol)
print(json.dumps(history, indent=2))
