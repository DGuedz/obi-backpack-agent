import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from core.risk_manager import RiskManager

async def deploy_sl():
    load_dotenv()
    transport = BackpackTransport()
    
    # We can reuse RiskManager to place SLs if it has the method, or call transport directly.
    # Transport has execute_order.
    
    print("️ DEPLOYING EMERGENCY SHIELDS (SL)...")
    
    positions = transport.get_positions()
    if not positions:
        print(" No positions to protect.")
        return

    orders = transport.get_open_orders()
    
    for pos in positions:
        symbol = pos['symbol']
        side = "LONG" if float(pos['netQuantity']) > 0 else "SHORT"
        qty = abs(float(pos['netQuantity']))
        entry = float(pos['entryPrice'])
        
        # Check if protected
        protected = False
        for order in orders:
            if order['symbol'] == symbol and order['orderType'] in ['StopLoss', 'StopLossLimit', 'StopMarket']:
                protected = True
                break
        
        if not protected:
            print(f"️ PROTECTING {symbol} ({side})...")
            
            # Calculate SL Price (5% Distance)
            sl_dist = entry * 0.05
            if side == "LONG":
                trigger_price = entry - sl_dist
                sl_side = "Ask"
            else:
                trigger_price = entry + sl_dist
                sl_side = "Bid"
                
            # Place Order
            # Endpoint: /api/v1/order
            # Payload: symbol, side, orderType="StopMarket", quantity, triggerPrice
            
            payload = {
                "symbol": symbol,
                "side": sl_side,
                "orderType": "Market",
                "quantity": str(qty),
                "triggerPrice": f"{trigger_price:.4f}",
                "triggerQuantity": str(qty)
            }
            
            res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            if res:
                print(f"    SL DEPLOYED AT {trigger_price:.4f}")
            else:
                print(f"    FAILED TO DEPLOY SL FOR {symbol}")
        else:
            print(f" {symbol} already protected.")

if __name__ == "__main__":
    asyncio.run(deploy_sl())
