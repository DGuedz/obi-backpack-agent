import sys
import os

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

def cancel_all():
    print("🧹 STARTING ORDER CLEANUP...")
    client = BackpackClient()
    
    # Target symbols
    symbols = ["SOL_USDC", "SOL_USDC_PERP"]
    
    for symbol in symbols:
        print(f"Checking {symbol}...")
        orders = client.get_open_orders(symbol)
        
        if orders:
            print(f"Found {len(orders)} open orders for {symbol}. Cancelling...")
            res = client.cancel_open_orders(symbol)
            print(f"Result: {res}")
        else:
            print(f"No open orders for {symbol}.")
            
    print("Order Cleanup Complete.")

if __name__ == "__main__":
    cancel_all()
