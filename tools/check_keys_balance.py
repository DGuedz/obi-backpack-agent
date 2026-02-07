
import os
import sys
import requests
import time
import base64
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def check_balance():
    print(" VERIFICANDO SALDOS DE TODAS AS CHAVES NO .ENV...")
    load_dotenv()

    # 1. MAIN WALLET
    print("\n1️⃣  [MAIN WALLET] (BACKPACK_API_KEY)")
    
    try:
        transport_main = BackpackTransport()
        
        # Debug Key Info
        print(f"   Key: {transport_main.auth.api_key[:10]}...")

        # TEST 1: GET /api/v1/capital (Spot Balances)
        print("    Querying /api/v1/capital (Balances)...")
        balances = transport_main._send_request("GET", "/api/v1/capital", "balanceQuery")
        print(f"   DEBUG RAW BALANCES: {balances}")
        
        usdc_balance = 0.0
        
        if balances:
            # Check standard format
            if isinstance(balances, dict) and 'USDC' in balances:
                 usdc_balance = float(balances['USDC'].get('available', 0))
            # Check list format (if any)
            elif isinstance(balances, list):
                 for b in balances:
                     if b.get('symbol') == 'USDC':
                         usdc_balance = float(b.get('available', 0))
        
        print(f"    USDC Balance (Spot/Capital): ${usdc_balance}")
        
        if not balances:
             print("    Balances empty.")

        # 3. Check Open Orders
        print("\n 3. Verificando Ordens Abertas...")
        try:
            open_orders = transport_main._send_request("GET", "/api/v1/orders", "orderQueryAll")
            if open_orders:
                print(f"   ️ Encontradas {len(open_orders)} ordens abertas:")
                for o in open_orders:
                    sym = o.get('symbol', 'Unknown')
                    side = o.get('side', 'Unknown')
                    qty = o.get('quantity', '0')
                    price = o.get('price', 'Market')
                    filled = o.get('executedQuantity', '0')
                    print(f"      - {sym} {side} {qty} @ {price} (Filled: {filled})")
            else:
                print("    Nenhuma ordem aberta encontrada.")
        except Exception as e:
            print(f"    Erro ao buscar ordens: {e}")

        # 4. Check Collateral (Futures)
        print("\n 4. Verificando Colateral (Futures)...")
        collateral = transport_main._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
        
        if collateral:
             print(f"    Futures Equity:         ${collateral.get('equity', 0)}")
             print(f"    Futures Avail to Trade: ${collateral.get('availableToTrade', 0)}")
        else:
             print("    Futures collateral info not found.")

        # 5. Check Active Positions (Perps)
        print("\n 5. Verificando Posições Perpétuas...")
        try:
            positions = transport_main._send_request("GET", "/api/v1/position", "positionQuery")
            if positions:
                print(f"   ️ Encontradas {len(positions)} posições abertas:")
                for p in positions:
                    print(f"      RAW POS: {p}")
                    print(f"      - {p.get('symbol')} | Side: {p.get('side')} | Qty: {p.get('quantity')} | PnL: {p.get('unrealizedPnl')}")
            else:
                print("    Nenhuma posição perpétua aberta.")
        except Exception as e:
            print(f"    Erro ao buscar posições: {e}")

    except Exception as e:
        print(f"    FALHA NA CHAVE PRINCIPAL: {e}")


if __name__ == "__main__":
    check_balance()
