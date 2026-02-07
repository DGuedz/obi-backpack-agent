import os
import sys
import asyncio
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def inspect():
    load_dotenv()
    transport = BackpackTransport()
    
    print(" Buscando 1 fill para inspeção...")
    fills = transport.get_fill_history(limit=1)
    
    if fills:
        print("RAW FILL OBJECT:")
        print(fills[0])
    else:
        print("Nenhum fill encontrado.")

if __name__ == "__main__":
    asyncio.run(inspect())
