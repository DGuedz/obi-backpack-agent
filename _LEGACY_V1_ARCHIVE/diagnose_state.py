import os
import json
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from dotenv import load_dotenv

def diagnose():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print("\n DIAGNOSTICANDO ESTADO ATUAL...")
    
    # 1. Posições
    print("\n POSIÇÕES ABERTAS:")
    positions = data.get_positions()
    if positions:
        for p in positions:
            print(f"   - {p['symbol']}: {p.get('quantity', p.get('netQuantity'))} (Entry: {p.get('entryPrice')})")
    else:
        print("   (Nenhuma posição aberta)")
        
    # 2. Ordens Abertas
    print("\n ORDENS ABERTAS:")
    orders = data.get_open_orders()
    if orders:
        for o in orders:
            # Print relevant details: ID, Symbol, Type, Side, Price, TriggerPrice
            print(f"   - [{o['id']}] {o['symbol']} {o['side']} {o['orderType']}")
            print(f"     Price: {o.get('price')} | Trigger: {o.get('triggerPrice')}")
            if 'stopLossTriggerPrice' in o:
                print(f"     ️ SL Trigger Attached: {o['stopLossTriggerPrice']}")
    else:
        print("   (Nenhuma ordem aberta)")

if __name__ == "__main__":
    diagnose()
