import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def check_info():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    markets = data.get_markets()
    fogo = next((m for m in markets if m['symbol'] == 'FOGO_USDC_PERP'), None)
    
    if fogo:
        print(f"Filters for FOGO_USDC_PERP:")
        print(f"  Step Size: {fogo.get('filters', {}).get('quantity', {}).get('stepSize')}")
        print(f"  Min Quantity: {fogo.get('filters', {}).get('quantity', {}).get('minQuantity')}")
        print(f"  Tick Size: {fogo.get('filters', {}).get('price', {}).get('tickSize')}")
    else:
        print("FOGO not found in markets.")

if __name__ == "__main__":
    check_info()
