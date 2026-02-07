
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

tickers = data.get_tickers()
if tickers:
    # Find a PERP ticker to check fields
    perp = next((t for t in tickers if 'PERP' in t['symbol']), None)
    if perp:
        print("PERP Sample:", perp)
    else:
        print("No PERP found in tickers.")
else:
    print("No tickers found")
