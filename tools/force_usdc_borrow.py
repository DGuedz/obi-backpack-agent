
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def force_borrow():
    print(" FORCE BORROW USDC: UNLOCKING VAULT")
    load_dotenv()
    transport = BackpackTransport()
    
    symbol = "USDC"
    # Borrow slightly less than max to avoid "Max Borrow" errors if any
    quantity = "40.0" 
    side = "Borrow"
    
    print(f"    Attempting to BORROW {quantity} {symbol}...")
    
    payload = {
        "symbol": symbol,
        "side": side,
        "quantity": quantity
    }
    
    try:
        # Instruction: borrowLendExecute
        res = transport._send_request("POST", "/api/v1/borrowLend", "borrowLendExecute", payload)
        print(f"    RESULTADO: {res}")
        
    except Exception as e:
        print(f"    ERRO CRÍTICO: {e}")

if __name__ == "__main__":
    force_borrow()
