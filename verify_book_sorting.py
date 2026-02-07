
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

symbol = "SOL_USDC_PERP"
depth = data.get_depth(symbol)

if depth and 'bids' in depth and 'asks' in depth:
    bids = depth['bids']
    asks = depth['asks']
    
    print(f"--- BOOK SORTING ANALYSIS ({symbol}) ---")
    print(f"Bids Count: {len(bids)}")
    if len(bids) > 1:
        print(f"Bid[0] (First): {bids[0]}")
        print(f"Bid[-1] (Last): {bids[-1]}")
        if float(bids[0][0]) > float(bids[-1][0]):
            print(" Bids are DESCENDING (High -> Low). Best Bid is [0].")
        else:
            print("️ Bids are ASCENDING (Low -> High). Best Bid is [-1].")
            
    print(f"Asks Count: {len(asks)}")
    if len(asks) > 1:
        print(f"Ask[0] (First): {asks[0]}")
        print(f"Ask[-1] (Last): {asks[-1]}")
        if float(asks[0][0]) < float(asks[-1][0]):
            print(" Asks are ASCENDING (Low -> High). Best Ask is [0].")
        else:
            print("️ Asks are DESCENDING (High -> Low). Best Ask is [-1].")
else:
    print("Failed to fetch depth.")
