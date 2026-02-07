import asyncio
import os
import sys
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def check_usdc():
    print(" VERIFICANDO SALDO USDC...")
    load_dotenv()
    transport = BackpackTransport()
    
    # Usando a mesma chamada que funcionou no probe
    data = transport._send_request("GET", "/api/v1/capital", "balanceQuery")
    
    if data:
        print(f"RAW KEYS: {list(data.keys())}")
        found_funds = False
        for asset, details in data.items():
            avail = float(details.get('available', 0))
            locked = float(details.get('locked', 0))
            staked = float(details.get('staked', 0))
            if avail > 0 or locked > 0 or staked > 0:
                print(f" {asset}: {details}")
                found_funds = True
        
        if not found_funds:
            print("️ NENHUM SALDO ENCONTRADO (Tudo Zero).")
    else:
        print(" Sem resposta.")

if __name__ == "__main__":
    asyncio.run(check_usdc())
