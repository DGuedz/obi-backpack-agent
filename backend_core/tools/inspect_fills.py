import os
import sys
import json
from datetime import datetime, timedelta

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backpacktrading/tools
project_root = os.path.dirname(current_dir) # .../backpacktrading
obi_core_path = os.path.join(project_root, 'obiwork_core')
core_path = os.path.join(obi_core_path, 'core')

sys.path.append(obi_core_path)
sys.path.append(core_path)

from backpack_transport import BackpackTransport
from dotenv import load_dotenv

load_dotenv()

def inspect_history():
    transport = BackpackTransport()
    
    print(" Buscando PnL History...")
    # Trying generic request to PnL endpoint
    pnl = transport._send_request("GET", "/api/v1/history/pnl", "pnlHistoryQuery", {"limit": "100"})
    
    if pnl:
        print(json.dumps(pnl[0] if len(pnl) > 0 else "Empty PnL List", indent=2))
    else:
        print(" Endpoint PnL não encontrado ou erro.")

if __name__ == "__main__":
    inspect_history()
