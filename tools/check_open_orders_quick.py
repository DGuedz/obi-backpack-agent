import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.backpack_transport import BackpackTransport

def check_open():
    transport = BackpackTransport()
    print(" Checking Open Orders...")
    orders = transport.get_open_orders()
    
    if orders:
        print(f" {len(orders)} Ordens Abertas:")
        for o in orders:
            print(f"   - {o['symbol']} {o['side']} {o['quantity']} @ ${o['price']} (Type: {o['orderType']})")
    else:
        print(" Nenhuma ordem aberta.")

if __name__ == "__main__":
    check_open()
