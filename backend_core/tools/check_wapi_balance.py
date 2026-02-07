import asyncio
import os
import sys
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def check_wapi():
    print(" VERIFICANDO SALDO WALLET (Spot/WAPI)...")
    load_dotenv()
    transport = BackpackTransport()
    
    # Tentativa 1: balanceQuery
    print("\n Tentando GET /wapi/v1/capital (balanceQuery)...")
    data = transport._send_request("GET", "/wapi/v1/capital", "balanceQuery")
    if data:
        print(f"RESPOSTA: {data}")
    else:
        print(" Falha na Tentativa 1.")

    # Tentativa 2: capitalQuery (caso a anterior falhe ou seja diferente)
    # print("\n Tentando GET /wapi/v1/capital (capitalQuery)...")
    # data2 = transport._send_request("GET", "/wapi/v1/capital", "capitalQuery")
    # if data2:
    #     print(f"RESPOSTA: {data2}")

if __name__ == "__main__":
    asyncio.run(check_wapi())
