import os
import sys
import json

# Add core path
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

from core.backpack_transport import BackpackTransport

def check_spot_usdc():
    print("️  VERIFICANDO SALDO SPOT (USDC)...", flush=True)
    transport = BackpackTransport() # Carrega do .env
    
    try:
        assets = transport.get_assets()
        if assets and 'USDC' in assets:
            avail = assets['USDC'].get('available', '0')
            locked = assets['USDC'].get('locked', '0')
            print(f"    USDC SPOT: Disponível={avail} | Bloqueado={locked}")
            
            if float(avail) > 0:
                print("    DINHEIRO ENCONTRADO NO SPOT!")
            else:
                print("   ️ USDC Spot Zerado.")
        else:
            print("   ️ USDC não encontrado na carteira Spot.")
            
    except Exception as e:
        print(f"    Erro: {e}")

if __name__ == "__main__":
    check_spot_usdc()
