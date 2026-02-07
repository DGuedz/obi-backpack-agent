import os
import sys
import json
import time

# Fix imports robustly
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

try:
    from core.backpack_transport import BackpackTransport
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.backpack_transport import BackpackTransport

def test_keys():
    print(" DIAGNÓSTICO DE CHAVES (OBI03 - MAIN WALLET)...", flush=True)
    
    # Chaves específicas fornecidas pelo usuário (.env atualizado)
    API_KEY = "ATAtTd1xZx/JGj6TLRfR0MHKWzvdKv1xRlA8ks+kRVY="
    API_SECRET = "lMBO+zflcOyrErjnbnE/YBp9rLgfDKs93XF/pR1mKM8="
    
    print(f" Testando Chave: {API_KEY[:10]}...", flush=True)
    
    # Instanciar Transport com chaves manuais
    transport = BackpackTransport(api_key=API_KEY, api_secret=API_SECRET)
    
    # 1. Teste de Conexão (Account)
    print("\n[1] Testando Autenticação (balanceQuery)...", flush=True)
    try:
        # Tentar ler saldo de Futures (Capital)
        collateral = transport.get_capital()
        print(f"   -> Resposta Futures: {collateral}")
        
        if collateral and isinstance(collateral, dict):
            if 'code' in collateral and collateral['code'] == 'INVALID_CLIENT_REQUEST':
                print("    Erro de Assinatura ou Permissão.")
            else:
                equity = collateral.get('totalEquity', '0')
                avail = collateral.get('availableToTrade', '0')
                print(f"    Conexão OK!")
                print(f"    Equity: {equity} | Available: {avail}")
        else:
            print("   ️ Resposta vazia ou inválida.")
            
    except Exception as e:
        print(f"    Exceção Futures: {e}")

    # 2. Teste de Spot (Assets)
    print("\n[2] Testando Saldo Spot (assetsQuery)...", flush=True)
    try:
        assets = transport.get_assets()
        print(f"   -> Resposta Spot: {assets}")
        
        if assets and isinstance(assets, dict):
             if 'USDC' in assets:
                 print(f"    USDC Spot: {assets['USDC']}")
             else:
                 print("   ️ USDC não encontrado no Spot.")
    except Exception as e:
        print(f"    Exceção Spot: {e}")

if __name__ == "__main__":
    test_keys()
