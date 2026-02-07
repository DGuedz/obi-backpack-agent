import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

def purge():
    print(" INICIANDO PURGE GERAL DE ORDENS (EMERGENCY CLEAR)...")
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # 1. Get All Open Orders
    orders = data.get_open_orders()
    if not orders:
        print(" Nenhuma ordem aberta encontrada.")
        return

    print(f" Encontradas {len(orders)} ordens abertas. Cancelando uma por uma...")
    
    # 2. Cancel Each Order
    for o in orders:
        symbol = o['symbol']
        order_id = o['id']
        print(f"    Cancelando {symbol} (ID: {order_id})...")
        
        # Try Cancel All for Symbol (More efficient if multiple orders per symbol)
        res = trade.cancel_open_orders(symbol)
        
        if res:
            print(f"       Sucesso.")
        else:
            print(f"      ️ Falha.")

if __name__ == "__main__":
    purge()
