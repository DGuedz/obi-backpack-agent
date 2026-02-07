import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

async def fix_orders():
    load_dotenv()
    transport = BackpackTransport()
    symbol = "BTC_USDC_PERP"
    
    print(f" FIXING ORDERS FOR {symbol}")
    
    # 1. Cancel All Open Orders
    print("   -> Cancelando todas as ordens abertas...")
    transport._send_request("DELETE", "/api/v1/orders", "orderCancelAll", {'symbol': symbol})
    
    # 2. Get Position
    positions = transport.get_positions()
    pos = next((p for p in positions if p['symbol'] == symbol), None)
    
    if not pos:
        print(" Nenhuma posição encontrada.")
        return

    qty = abs(float(pos.get('netQuantity', pos.get('quantity'))))
    entry = float(pos.get('entryPrice'))
    side = "Short" if float(pos.get('netQuantity', pos.get('quantity'))) < 0 else "Long"
    
    print(f"   -> Posição: {side} {qty} @ {entry}")
    
    # 3. Calculate TP/SL
    if side == "Short":
        tp_price = round(entry * 0.995, 1) # 0.5% Lucro (5% ROE)
        sl_price = round(entry * 1.005, 1) # 0.5% Perda
        tp_side = "Bid"
        sl_side = "Bid" # Stop Market de Compra fecha Short
    else:
        tp_price = round(entry * 1.005, 1)
        sl_price = round(entry * 0.995, 1)
        tp_side = "Ask"
        sl_side = "Ask"
        
    print(f"   -> Definindo TP: {tp_price} | SL: {sl_price}")
    
    # 4. Place TP (Limit Maker)
    payload_tp = {
        "symbol": symbol,
        "side": tp_side,
        "orderType": "Limit",
        "quantity": str(qty),
        "price": str(tp_price),
        "postOnly": True
    }
    res_tp = transport._send_request("POST", "/api/v1/order", "orderExecute", payload_tp)
    print(f"    TP Enviado: {res_tp.get('id') if res_tp else 'Erro'}")
    
    # 5. Place SL (Stop Market)
    payload_sl = {
        "symbol": symbol,
        "side": sl_side,
        "orderType": "Market",
        "quantity": str(qty),
        "triggerPrice": str(sl_price),
        "triggerQuantity": str(qty)
    }
    res_sl = transport._send_request("POST", "/api/v1/order", "orderExecute", payload_sl)
    print(f"    SL Enviado: {res_sl.get('id') if res_sl else 'Erro'}")

if __name__ == "__main__":
    asyncio.run(fix_orders())
