import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport

load_dotenv()

def test_stop_loss():
    transport = BackpackTransport()
    symbol = "BTC_USDC_PERP"
    
    print(" Testando Stop Loss Order...")
    
    # 1. Teste com triggerQuantity
    print("\n--- Teste 1: Market + TriggerPrice + TriggerQuantity ---")
    payload = {
        "symbol": symbol,
        "side": "Ask", 
        "orderType": "Market",
        "quantity": "0.001",
        "triggerPrice": "80000.0",
        "triggerQuantity": "0.001"
    }
    print(f" Payload: {payload}")
    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
    if res and 'id' in res:
        print(f" Sucesso: {res['id']}")
        # Cancelar logo em seguida
        transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': res['id']})
    else:
        print(" Falha")

    # 2. Teste StopMarket (Se existir)
    print("\n--- Teste 2: StopMarket ---")
    payload = {
        "symbol": symbol,
        "side": "Ask", 
        "orderType": "StopMarket",
        "quantity": "0.001",
        "triggerPrice": "80000.0"
    }
    print(f" Payload: {payload}")
    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
    if res and 'id' in res:
        print(f" Sucesso: {res['id']}")
        transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': res['id']})
    else:
        print(" Falha")

if __name__ == "__main__":
    test_stop_loss()
