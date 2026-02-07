import os
import sys
from dotenv import load_dotenv

# Adiciona o diretório atual (root) ao path
sys.path.append(os.getcwd())
# Adiciona diretórios auxiliares
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport

def cancel_specific_order():
    load_dotenv()
    
    transport = BackpackTransport()
    
    # ID da ordem redundante identificada no check_status
    order_id = "29243694283"
    symbol = "SKR_USDC_PERP"
    
    print(f" TARGET REMOVAL: Cancelling redundant order {order_id} for {symbol}...")
    
    try:
        result = transport.cancel_order(symbol, order_id)
        print(f" Cancel Request Sent.")
        print(f"   Result: {result}")
    except Exception as e:
        print(f" Failed to cancel order: {e}")

if __name__ == "__main__":
    cancel_specific_order()
