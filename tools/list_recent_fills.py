import sys
import os
import time
import requests
import json
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport

def list_recent_orders():
    print(" LISTAGEM DE ORDENS RECENTES (Últimas 24h)")
    transport = BackpackTransport()
    
    # Filtrar por Fill History (Execuções)
    # /api/v1/history/fills?limit=20
    
    try:
        # endpoint: /wapi/v1/history/fills
        # instruction: fillHistoryQueryAll
        fills = transport.get_fill_history(limit=20)
        
        if not fills:
            print("   ℹ️ Nenhuma execução encontrada nas últimas ordens.")
            return

        print(f"    Encontradas {len(fills)} execuções recentes:\n")
        
        for fill in fills:
            symbol = fill.get('symbol')
            side = fill.get('side')
            price = fill.get('price')
            qty = fill.get('quantity')
            fee = fill.get('fee', '0')
            ts = fill.get('timestamp') # Pode ser string ou int
            
            # Converter timestamp
            try:
                # Se for string ISO, ok. Se for int ms, converter.
                # Backpack costuma usar string ISO ou int ms?
                # Vamos assumir int ms se for numérico
                if str(ts).isdigit():
                    dt_obj = datetime.datetime.fromtimestamp(int(ts)/1000)
                    time_str = dt_obj.strftime('%H:%M:%S')
                else:
                    time_str = str(ts)
            except:
                time_str = "Unknown Time"

            print(f"   ⏰ {time_str} | {symbol} | {side.upper()} | Qty: {qty} @ {price} | Fee: ${fee}")
            
    except Exception as e:
        print(f"    Erro ao buscar histórico: {e}")

if __name__ == "__main__":
    list_recent_orders()
