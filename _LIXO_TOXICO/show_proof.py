
import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def show_proof():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print("\n PROVA DE PROTEÇÃO (GUARDIAN PROOF)")
    print("=======================================")
    
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    if not positions:
        print("Nenhuma posição aberta.")
        return

    for p in positions:
        symbol = p['symbol']
        qty = float(p['netQuantity'])
        if qty == 0: continue
        
        side = "LONG" if qty > 0 else "SHORT"
        entry = float(p['entryPrice'])
        
        print(f"\n {symbol} | {side} | Entry: {entry}")
        
        # Find Stops
        stops = [o for o in orders if o['symbol'] == symbol and o['triggerPrice'] is not None]
        limits = [o for o in orders if o['symbol'] == symbol and o['orderType'] == 'Limit' and o['triggerPrice'] is None]
        
        if stops:
            print("    STOP LOSS DETECTADO:")
            for s in stops:
                trigger = s['triggerPrice']
                print(f"      - ID: {s['id']} | Trigger: {trigger} (Market)")
        else:
            print("    SEM STOP LOSS (PERIGO!)")
            
        if limits:
            print("    TAKE PROFIT DETECTADO:")
            for l in limits:
                price = l['price']
                # Filter out far away orders that might be entry orders? 
                # Assuming limits are TPs for now if side matches exit
                print(f"      - ID: {l['id']} | Alvo: {price}")
        else:
            print("   ️ SEM TAKE PROFIT VISÍVEL")

if __name__ == "__main__":
    show_proof()
