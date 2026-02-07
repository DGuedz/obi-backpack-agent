print("DEBUG: Script Starting...")
import os
import sys
print("DEBUG: Imports...")

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

try:
    from backpack_transport import BackpackTransport
    print("DEBUG: BackpackTransport Imported")
except ImportError as e:
    print(f"DEBUG: Import Error: {e}")
    sys.exit(1)

from dotenv import load_dotenv
import requests
import json

def undo_lending():
    print(" UNDO LENDING PROTOCOL (Resgate de Margem)")
    load_dotenv()
    
    # Use Main Wallet
    try:
        transport = BackpackTransport()
        print("DEBUG: Transport Initialized")
    except Exception as e:
        print(f"DEBUG: Transport Init Error: {e}")
        return

    # 1. Consultar Posições de Empréstimo (Lend/Borrow)
    print("\n 1. Buscando Posições de Lending...")
    try:
        # Instruction: borrowLendPositionQuery
        positions = transport._send_request("GET", "/api/v1/borrowLend/positions", "borrowLendPositionQuery")
        
        if positions is None:
             print("   ️ Erro na consulta (None returned).")
        elif not positions:
            print("    Nenhuma posição de Lending encontrada (Lista Vazia).")
        else:
            print(f"    Posições Encontradas: {len(positions)}")
            for p in positions:
                print(f"      - {p}")
                
            for p in positions:
                symbol = p.get('symbol')
                qty_str = p.get('netQuantity', "0")
                try:
                    qty = float(qty_str)
                except:
                    qty = 0.0
                
                print(f"      Analysing: {symbol} | NetQty: {qty}")
                
                # Filter for significant amounts
                if qty > 0.0001: 
                    print(f"\n 2. Iniciando Saque de {qty} {symbol}...")
                    
                    # FORCE BORROW STRATEGY
                    # To unlock "Lent" funds for trading, we Borrow against them.
                    # We will Borrow 95% of the Lent amount to be safe.
                    borrow_qty = qty * 0.95
                    borrow_qty_str = f"{borrow_qty:.2f}"
                    
                    print(f"    Tentativa FORCE BORROW: {borrow_qty_str} (Side: Borrow)...")
                    payload3 = {
                        "symbol": symbol,
                        "side": "Borrow",
                        "quantity": borrow_qty_str
                    }
                    
                    # Manual Request Handling to avoid 'Expecting value' error on empty 200 OK
                    url = f"{transport.base_url}/api/v1/borrowLend"
                    headers = transport.auth.get_headers("borrowLendExecute", payload3)
                    
                    try:
                        raw_res = requests.post(url, headers=headers, json=payload3)
                        
                        if raw_res.status_code == 200:
                            print(f"    SUCESSO (Status 200)! Pedido de Saque/Borrow enviado.")
                            # Try parsing just for info, but don't fail
                            try:
                                print(f"      Response: {raw_res.json()}")
                            except:
                                print("      (Body vazio, mas sucesso confirmado pelo status 200)")
                        else:
                            print(f"    Falha Tentativa 3. Status: {raw_res.status_code} | {raw_res.text}")
                    except Exception as e:
                        print(f"    Erro de Conexão: {e}")

    except Exception as e:
        print(f"    Erro Crítico: {e}")

    # Checagem Final
    print("\n 3. Verificando Saldos (Spot & Futures)...")
    
    # Check Spot
    try:
        # Use raw request for assets to avoid transport error on empty list? No, assets usually returns dict.
        assets = transport.get_assets()
        print(f"    Spot Assets Raw: {assets}")
        
        found_usdc = False
        if isinstance(assets, dict):
            # Check for USDC
            usdc = assets.get('USDC')
            if usdc:
                avail = float(usdc.get('available', 0))
                print(f"      - USDC Available: {avail}")
                if avail > 0.01:
                    found_usdc = True
                    print(f"       Transferindo {avail} USDC para Futures...")
                    dep_payload = {
                        "symbol": "USDC",
                        "quantity": str(avail),
                        "from": "spot",
                        "to": "futures"
                    }
                    # depositCollateral usually returns success
                    dep_res = transport._send_request("POST", "/wapi/v1/capital/deposit", "depositCollateral", dep_payload)
                    if dep_res:
                        print("       Transferência Concluída!")
                    else:
                        # Fallback: Maybe it's already in futures?
                        pass
        
        if not found_usdc:
            print("      (Nenhum saldo USDC significativo no Spot)")

    except Exception as e:
        print(f"   ️ Erro ao checar Spot: {e}")

    try:
        collateral = transport.get_account_collateral()
        if collateral:
            print(f"    Futures USDC Disponível: ${collateral.get('availableToTrade', '0.00')}")
    except:
        pass

if __name__ == "__main__":
    undo_lending()
