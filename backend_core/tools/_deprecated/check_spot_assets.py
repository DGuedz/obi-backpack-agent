import asyncio
import os
import sys
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def check_spot():
    print(" VERIFICANDO SALDO SPOT...")
    load_dotenv()
    transport = BackpackTransport()
    
    try:
        assets = transport.get_assets()
        print("\n SALDO SPOT (Filtrado > 0):")
        
        # Check if assets is a dict (like futures) or list
        if isinstance(assets, dict):
            for symbol, data in assets.items():
                if float(data.get('available', 0)) > 0 or float(data.get('locked', 0)) > 0:
                    print(f"   {symbol}: {data}")
        elif isinstance(assets, list):
            found = False
            for asset in assets:
                # Assuming structure based on previous output or standard
                # If it's the market definition list, it might not have balance.
                # But assetsQuery SHOULD return balances.
                # Let's check keys of one item
                if 'available' in asset or 'balance' in asset:
                    avail = float(asset.get('available', 0))
                    locked = float(asset.get('locked', 0))
                    if avail > 0 or locked > 0:
                        print(f"   {asset.get('symbol')}: Avail={avail} Locked={locked}")
                        found = True
            if not found:
                 print("   (Nenhum saldo > 0 encontrado na lista)")
                 # Print one item to debug structure
                 if assets:
                     print(f"   DEBUG Structure (first item): {assets[0]}")
        else:
            print(f"   Unknown format: {type(assets)}")
            
    except Exception as e:
        print(f" Erro ao ler assets: {e}")

if __name__ == "__main__":
    asyncio.run(check_spot())
