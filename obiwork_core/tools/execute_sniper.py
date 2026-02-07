import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

async def execute_sniper(symbol, side, leverage, amount, sl_price, tp_price):
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    transport = BackpackTransport()
    
    print(f" INICIANDO SNIPER EXECUTION: {symbol} ({side})")
    print(f" Capital: ${amount} | Lev: {leverage}x")
    print(f"️ SL: {sl_price} |  TP: {tp_price}")
    
    # 1. Get Current Price
    ticker = data.get_ticker(symbol)
    if not ticker:
        print(" Erro ao obter preço atual.")
        return
    
    current_price = float(ticker['lastPrice'])
    print(f" Preço Atual: {current_price}")
    
    # 2. Calculate Quantity
    # Notional = Amount * Leverage
    # Qty = Notional / Price
    notional = amount * leverage
    qty = notional / current_price
    
    # Adjust precision (assuming 2 decimals for quantity for ETH - check filters in prod)
    # Getting filters
    filters = data.get_market_filters(symbol)
    step_size = filters.get('stepSize', 0.01)
    
    # Round quantity to stepSize
    qty = int(qty / step_size) * step_size
    qty = round(qty, 2) # Safe fallback
    
    print(f"️ Quantidade Calculada: {qty} {symbol.split('_')[0]}")
    
    # 3. Execute Market Order (Entry)
    print(" Enviando Ordem a Mercado...")
    order_side = "Bid" if side.upper() == "LONG" else "Ask"
    
    payload = {
        "symbol": symbol,
        "side": order_side,
        "orderType": "Market",
        "quantity": str(qty)
    }
    
    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
    
    if res and 'id' in res:
        print(f" Entrada Confirmada! ID: {res['id']}")
        
        # 4. Set Stop Loss
        print("️ Configurando Stop Loss...")
        sl_side = "Ask" if side.upper() == "LONG" else "Bid"
        
        # FIX: Backpack API uses 'Market' or 'Limit' with triggerPrice, not 'StopMarket' as a type directly in some contexts
        # But per documentation, Trigger Orders are usually Market/Limit with trigger params.
        # Let's try 'Market' with triggerPrice which acts as Stop Market.
        
        sl_payload = {
            "symbol": symbol,
            "side": sl_side,
            "orderType": "Market", # Use Market for Stop Market behavior
            "quantity": str(qty),
            "triggerPrice": str(sl_price)
        }
        sl_res = transport._send_request("POST", "/api/v1/order", "orderExecute", sl_payload)
        if sl_res and 'id' in sl_res:
            print(f" SL Armado em {sl_price}")
        else:
            print(f" Falha ao armar SL: {sl_res}")
            
        # 5. Set Take Profit
        print(" Configurando Take Profit...")
        tp_payload = {
            "symbol": symbol,
            "side": sl_side,
            "orderType": "Limit",
            "quantity": str(qty),
            "price": str(tp_price),
            "postOnly": True
        }
        tp_res = transport._send_request("POST", "/api/v1/order", "orderExecute", tp_payload)
        if tp_res and 'id' in tp_res:
            print(f" TP Armado em {tp_price}")
        else:
            print(f" Falha ao armar TP: {tp_res}")
            
    else:
        print(f" Falha na Entrada: {res}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--side", type=str, required=True)
    parser.add_argument("--leverage", type=int, required=True)
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--sl", type=float, required=True)
    parser.add_argument("--tp", type=float, required=True)
    
    args = parser.parse_args()
    
    asyncio.run(execute_sniper(args.symbol, args.side, args.leverage, args.amount, args.sl, args.tp))
