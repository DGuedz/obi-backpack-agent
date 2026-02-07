import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def list_protections():
    print("️ VERIFICAÇÃO DE BLINDAGEM (STOPS & ALVOS)")
    print("============================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # 1. Posições Abertas
    positions = data.get_positions()
    open_positions = [p for p in positions if float(p['netQuantity']) != 0]
    
    # 2. Ordens Abertas
    orders = data.get_open_orders()
    
    print(f" POSIÇÕES ATIVAS: {len(open_positions)}")
    print(f" ORDENS PENDENTES (Total): {len(orders)}\n")
    
    for pos in open_positions:
        symbol = pos['symbol']
        qty = float(pos['netQuantity'])
        entry = float(pos['entryPrice'])
        side = "LONG" if qty > 0 else "SHORT"
        
        print(f" {symbol} | {side} {abs(qty)} @ {entry}")
        
        # Filtrar ordens deste símbolo
        my_orders = [o for o in orders if o['symbol'] == symbol]
        
        sl_found = False
        tp_found = False
        
        for o in my_orders:
            o_type = o['orderType']
            o_side = o['side']
            o_price = o.get('price')
            o_trigger = o.get('triggerPrice')
            
            # Identificar Stop Loss (Gatilho)
            if o_trigger:
                print(f"    STOP LOSS (Gatilho): ${o_trigger} ({o_type})")
                sl_found = True
                
            # Identificar Take Profit (Limit contra a posição)
            elif o_type == "Limit" and not o_trigger:
                # Verificar se é contra a posição (Venda se Long)
                if (side == "LONG" and o_side == "Ask") or (side == "SHORT" and o_side == "Bid"):
                    print(f"    TAKE PROFIT (Alvo):  ${o_price}")
                    tp_found = True
        
        if not sl_found:
            print("   ️ PERIGO: SEM STOP LOSS DETECTADO!")
        if not tp_found:
            print("   ️ AVISO: SEM TAKE PROFIT DEFINIDO.")
        print("-" * 40)

if __name__ == "__main__":
    list_protections()
