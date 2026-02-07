
import os
import sys
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

load_dotenv()

auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

print("--- OPEN POSITIONS (ACTIVE) ---")
positions = data.get_positions()
if positions:
    for p in positions:
        print(f" {p['symbol']} | Side: {p.get('side', 'N/A')} | PnL: {p.get('unrealizedPnl', 0)}")
else:
    print(" Nenhuma posição aberta.")

print("\n--- OPEN ORDERS (LIMIT/WAITING) ---")
orders = data.get_open_orders()
if orders:
    for o in orders:
        price = o.get('price', 'MARKET') # Se for Market Order não tem preço fixo
        qty = o.get('quantity', 0)
        print(f"⏳ {o['symbol']} | {o['side']} | Price: {price} | Qty: {qty}")
else:
    print(" Nenhuma ordem pendente no book.")
