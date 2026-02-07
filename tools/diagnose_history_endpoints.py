import sys
import os
import time
import requests
import json
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport

def diagnose_history():
    print("️‍️ DIAGNÓSTICO DE ENDPOINTS DE HISTÓRICO")
    transport = BackpackTransport()
    
    # TESTE 1: /wapi/v1/history/fills (fillHistoryQueryAll) - Já testado, deu 404?
    # Vamos retestar com instruction correta
    print("\n[1] TESTE /wapi/v1/history/fills (Instruction: fillHistoryQueryAll)")
    try:
        # Nota: O BackpackTransport.get_fill_history já foi corrigido para passar params no GET.
        # Vamos chamar direto o método corrigido.
        fills = transport.get_fill_history(limit=5)
        if fills is not None:
             print(f"    SUCESSO! {len(fills)} fills encontrados.")
        else:
             print("    Falha (None returned).")
    except Exception as e:
        print(f"    Erro: {e}")

    # TESTE 2: /api/v1/history/orders (orderHistoryQueryAll)
    print("\n[2] TESTE /api/v1/history/orders (Instruction: orderHistoryQueryAll)")
    try:
        orders = transport.get_order_history(limit=5)
        if orders is not None:
             print(f"    SUCESSO! {len(orders)} ordens encontradas.")
             # Printar detalhes para ver status Filled
             for o in orders:
                 print(f"      - {o.get('symbol')} {o.get('side')} {o.get('status')} {o.get('executedQuantity')}")
        else:
             print("    Falha (None returned).")
    except Exception as e:
        print(f"    Erro: {e}")
        
    # TESTE 3: /wapi/v1/history/orders (orderHistoryQueryAll) - Endpoint alternativo
    print("\n[3] TESTE /wapi/v1/history/orders (Instruction: orderHistoryQueryAll)")
    try:
        endpoint = "/wapi/v1/history/orders"
        params = {"limit": "5", "offset": "0"}
        res = transport._send_request("GET", endpoint, "orderHistoryQueryAll", params)
        if res is not None:
             print(f"    SUCESSO! {len(res)} ordens encontradas via WAPI.")
        else:
             print("    Falha (None returned).")
    except Exception as e:
        print(f"    Erro: {e}")

if __name__ == "__main__":
    diagnose_history()
