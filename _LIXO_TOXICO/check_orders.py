import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def check_orders():
    api_key = os.getenv('BACKPACK_API_KEY')
    private_key = os.getenv('BACKPACK_API_SECRET')
    
    if not api_key:
        print("API Key missing")
        return

    auth = BackpackAuth(api_key, private_key)
    data = BackpackData(auth)
    
    print("Fetching Open Orders...")
    orders = data.get_open_orders()
    
    eth_orders = [o for o in orders if o.get('symbol') == 'ETH_USDC_PERP']
    
    print(f"Total Open Orders: {len(orders)}")
    print(f"ETH Orders: {len(eth_orders)}")
    
    for o in eth_orders:
        print(f" - {o.get('side')} {o.get('orderType')} {o.get('price')} (Qty: {o.get('quantity')}) ReduceOnly: {o.get('reduceOnly')}")

if __name__ == "__main__":
    check_orders()
