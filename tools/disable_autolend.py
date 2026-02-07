
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def disable_autolend():
    print(" DISABLING AUTO-LEND...")
    load_dotenv()
    transport = BackpackTransport()
    
    payload = {
        "autoLend": False
    }
    
    try:
        # Instruction: accountUpdate
        res = transport._send_request("PATCH", "/api/v1/account", "accountUpdate", payload)
        print(f"    Settings Updated: {res}")
        
    except Exception as e:
        print(f"    Erro ao atualizar settings: {e}")

if __name__ == "__main__":
    disable_autolend()
