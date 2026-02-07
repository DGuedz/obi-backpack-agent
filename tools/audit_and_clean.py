import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport

def audit_and_clean():
    print(" AUDIT & CLEANUP PROTOCOL STARTED")
    transport = BackpackTransport()
    
    # 1. Verificar Histórico Recente (Últimos 5 fills) para entender o que aconteceu
    print("\n RECENT FILL HISTORY:")
    fills = transport.get_fill_history(limit=10)
    if fills:
        for fill in fills:
            symbol = fill.get('symbol')
            side = fill.get('side')
            price = fill.get('price')
            qty = fill.get('quantity')
            fee = fill.get('fee', 0)
            time_ = fill.get('timestamp')
            print(f"   -> {symbol} {side} @ {price} (Qty: {qty}) | Fee: {fee}")
    else:
        print("   -> No recent fills found (or API error).")

    # 2. Cancelar Ordens Órfãs (Liberar Margem)
    print("\n RELEASING MARGIN (Canceling Open Orders)...")
    open_orders = transport.get_open_orders()
    if open_orders:
        for order in open_orders:
            oid = order.get('id')
            symbol = order.get('symbol')
            side = order.get('side')
            type_ = order.get('orderType')
            print(f"    Canceling {symbol} {side} {type_} (ID: {oid})...")
            transport.cancel_order(symbol, oid)
    else:
        print("   -> No open orders to cancel.")
        
    # 3. Verificar Saldo Real (Debug Profundo)
    print("\n FINAL BALANCE CHECK:")
    capital = transport.get_account_collateral()
    print(f"   -> RAW CAPITAL DATA: {capital}")
    if capital and 'USDC' in capital:
        usdc = capital['USDC']
        avail = usdc.get('availableToTrade', 0)
        locked = usdc.get('locked', 0)
        print(f"   -> USDC Available to Trade: {avail}")
        print(f"   -> USDC Locked: {locked}")

if __name__ == "__main__":
    audit_and_clean()
