import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

print("--- POSITIONS ---")
positions = data.get_positions()
for p in positions:
    if float(p['netQuantity']) != 0:
        print(p)

print("\n--- OPEN ORDERS (ALL) ---")
orders = data.get_open_orders()
for o in orders:
    print(f"{o['symbol']} | {o['side']} | {o['orderType']} | Price: {o['price']} | Qty: {o['quantity']}")
