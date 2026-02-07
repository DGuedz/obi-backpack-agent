import sys
import os
import json
import time
import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport

def fix_lending():
    print(" INICIANDO CORREÇÃO DE LENDING E LIBERAÇÃO DE COLATERAL...")
    sys.stdout.flush()
    
    transport = BackpackTransport()
    
    # 1. OBTER QUANTIDADE EXATA EM LENDING
    print("\n[1] Obtendo quantidade exata de USDC em Lending...")
    lending_qty = "0"
    try:
        positions = transport._send_request("GET", "/api/v1/borrowLend/positions", "borrowLendPositionQuery")
        if positions:
            for pos in positions:
                if pos.get('symbol') == 'USDC':
                    lending_qty = pos.get('netQuantity', "0")
                    print(f"    Alvo Identificado: {lending_qty} USDC em Lending.")
                    break
    except Exception as e:
        print(f"    Erro ao ler posições: {e}")
        return

    if float(lending_qty) <= 0:
        print("    Nada para liberar (Lending <= 0).")
        return

    # 2. EXECUTAR BORROW PARA ANULAR LENDING
    print(f"\n[2] Executando 'Borrow' de {lending_qty} USDC para anular Lending...")
    
    payload = {
        "symbol": "USDC",
        "side": "Borrow",
        "quantity": lending_qty
    }
    
    # Usar requests direto para melhor controle de erro
    url = f"{transport.base_url}/api/v1/borrowLend"
    headers = transport.auth.get_headers("borrowLendExecute", payload)
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            print("    SUCESSO! Ordem de Borrow enviada (Status 200).")
            print(f"   Response: {res.text}")
        else:
            print(f"    FALHA. Status: {res.status_code}")
            print(f"   Response: {res.text}")
    except Exception as e:
        print(f"    Erro de conexão: {e}")

    # 3. VERIFICAR RESULTADO
    print("\n[3] Verificando novo saldo disponível em Futures...")
    time.sleep(2)
    try:
        collateral = transport._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
        if collateral and 'collateral' in collateral:
            for asset in collateral['collateral']:
                if asset.get('symbol') == 'USDC':
                    avail = asset.get('availableQuantity', '0')
                    print(f"    Novo Saldo Disponível USDC: {avail}")
                    if float(avail) > 0:
                        print("    SUCESSO! Saldo liberado para uso em Futures.")
                    else:
                        print("   ️ AVISO: Saldo disponível ainda é 0. Pode haver delay ou bloqueio.")
    except Exception as e:
        print(f"    Erro ao verificar saldo: {e}")

if __name__ == "__main__":
    fix_lending()
