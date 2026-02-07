
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def audit_positions():
    transport = BackpackTransport()
    print("️ OBI FULL ACCOUNT AUDIT")
    
    # 1. Check Perp Positions (BTC, SOL, etc.)
    print("\n1. Checking Perpetual Positions...")
    try:
        positions = transport.get_positions()
        if positions:
            for p in positions:
                symbol = p.get('symbol')
                side = p.get('side')
                size = p.get('quantity')
                entry = p.get('entryPrice')
                pnl = p.get('unrealizedPnl')
                print(f"   ️ ACTIVE PERP: {side} {size}x {symbol} @ ${entry} (PnL: {pnl})")
        else:
            print("    No active Perp positions.")
    except Exception as e:
        print(f"    Error checking perps: {e}")

    # 2. Check Open Orders (Limit Orders waiting to fill)
    print("\n2. Checking Open Orders (Limit)...")
    try:
        orders = transport.get_open_orders()
        if orders:
            for o in orders:
                symbol = o.get('symbol')
                side = o.get('side')
                price = o.get('price')
                qty = o.get('quantity')
                status = o.get('status')
                print(f"   ⏳ OPEN ORDER: {side} {qty}x {symbol} @ ${price} ({status})")
        else:
            print("    No open orders found.")
    except Exception as e:
        print(f"    Error checking orders: {e}")

if __name__ == "__main__":
    audit_positions()
