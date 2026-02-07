import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport

def probe_balance():
    print(" PROBE BALANCE: Testing Margin Capability...")
    
    transport = BackpackTransport()
    
    # 1. Tentar ler saldo com 'capitalQuery' (Standard)
    print("\n Probing with 'capitalQuery' instruction...")
    try:
        # Forçar o uso de 'capitalQuery' no request
        # Hack: Vamos chamar _send_request diretamente
        response = transport._send_request("GET", "/api/v1/capital", "capitalQuery")
        print(f"   Result: {json.dumps(response)[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Tentar ler saldo com 'balanceQuery' (Alternative used in current transport)
    print("\n Probing with 'balanceQuery' instruction...")
    try:
        response = transport._send_request("GET", "/api/v1/capital", "balanceQuery")
        print(f"   Result: {json.dumps(response)[:200]}...")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Tentar colocar ordem Limit (Probe)
    # Comprar 0.01 SOL a $100.00 (Mais perto, mas ainda seguro)
    # Preço atual SOL ~117.
    # $100 é razoável.
    print("\n Probing with Dummy Order (Buy 0.01 SOL @ $100.00)...")
    try:
        order = transport.execute_order(
            symbol="SOL_USDC_PERP",
            side="Bid",
            order_type="Limit",
            quantity="0.01",
            price="100.00"
        )
        if order and order.get('id'):
            print(f"    ORDER ACCEPTED! ID: {order.get('id')}")
            print("    CONCLUSION: Margin IS available. API Read is broken.")
            print("    Canceling probe order...")
            transport.cancel_order("SOL_USDC_PERP", order.get('id'))
        else:
            print(f"    Order Rejected or Failed: {order}")
    except Exception as e:
        print(f"    Execution Exception: {e}")

if __name__ == "__main__":
    probe_balance()
