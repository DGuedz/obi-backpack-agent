import os
import sys
import asyncio
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

async def fix_sl_lit():
    load_dotenv()
    transport = BackpackTransport()
    
    symbol = "LIT_USDC_PERP"
    qty = "176.6" # Quantidade exata calculada no log anterior
    sl_price = "1.75"
    
    print(f"️ Configurando Stop Loss Manual para {symbol}...")
    print(f"   Qtd: {qty} | Trigger: {sl_price}")
    
    # Payload Correto: Market Order com triggerPrice E triggerQuantity
    # A API da Backpack exige ambos para Trigger Orders
    payload = {
        "symbol": symbol,
        "side": "Bid", # Comprar para sair do Short
        "orderType": "Market", 
        "quantity": qty,
        "triggerPrice": sl_price,
        "triggerQuantity": qty # Fix crítico
    }
    
    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
    
    if res and 'id' in res:
        print(f" SL Armado com Sucesso! ID: {res['id']}")
    else:
        print(f" Falha ao armar SL: {res}")

if __name__ == "__main__":
    asyncio.run(fix_sl_lit())
