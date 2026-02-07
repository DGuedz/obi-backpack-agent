import os
import sys
import asyncio
from tabulate import tabulate
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
# from backpack_auth import BackpackAuth
# from backpack_data import BackpackData

async def check_sl_status():
    load_dotenv()
    
    transport = BackpackTransport()
    # auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    # data_client = BackpackData(auth)
    
    print(" VERIFICANDO STATUS DE PROTEÇÃO (SL)...")
    
    # 1. Get Positions
    positions = transport.get_positions()
    if not positions:
        print(" Nenhuma posição aberta.")
        return

    # DEBUG: Print first position to see structure
    if positions:
        print(f"DEBUG POS: {positions[0]}")

    # 2. Get Open Orders
    orders = transport.get_open_orders()
    if orders:
        print(f"DEBUG ORDERS COUNT: {len(orders)}")
        print(f"DEBUG FIRST ORDER: {orders[0]}")
    
    report = []
    
    for pos in positions:
        symbol = pos['symbol']
        side = "LONG" if float(pos['netQuantity']) > 0 else "SHORT"
        qty = float(pos['netQuantity'])
        entry = float(pos['entryPrice'])
        mark = float(pos['markPrice'])
        
        # Check for SL Order
        sl_order = None
        for order in orders:
            is_stop = False
            # Check explicit types
            if order['orderType'] in ['StopLoss', 'StopLossLimit', 'StopMarket']:
                is_stop = True
            # Check conditional market/limit
            elif order['triggerPrice'] is not None:
                is_stop = True
            
            if order['symbol'] == symbol and is_stop:
                # Verify direction (Long needs Sell SL, Short needs Buy SL)
                order_side = order['side']
                if (side == "LONG" and order_side == "Ask") or (side == "SHORT" and order_side == "Bid"):
                    sl_order = order
                    break
        
        status = "️ PROTECTED" if sl_order else "️ NAKED (PERIGO)"
        sl_price = float(sl_order['triggerPrice']) if sl_order else 0.0
        
        pnl_pct = ((mark - entry) / entry) * 100 if side == "LONG" else ((entry - mark) / entry) * 100
        
        report.append([
            symbol, side, qty, f"{entry:.4f}", f"{mark:.4f}", f"{pnl_pct:+.2f}%", 
            f"{sl_price:.4f}" if sl_order else "---", status
        ])
        
    print(tabulate(report, headers=["Symbol", "Side", "Qty", "Entry", "Mark", "PnL %", "SL Price", "Status"], tablefmt="fancy_grid"))
    
    naked_count = sum(1 for r in report if "NAKED" in r[7])
    if naked_count > 0:
        print(f"\n ALERTA: {naked_count} POSIÇÕES DESPROTEGIDAS! O SL SONAR DEVE CORRIGIR EM BREVE.")
    else:
        print("\n TODAS AS POSIÇÕES ESTÃO PROTEGIDAS.")

if __name__ == "__main__":
    asyncio.run(check_sl_status())
