import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

# Configuration
SL_PERCENT = 0.15  # 15% Stop Loss for Night Mode (Wide Survival)
LEVERAGE = 1       # Assuming 1x based on previous check, but SL is based on price distance

async def main():
    print(" INICIANDO PROTOCOLO NIGHT GUARD (WIDE SURVIVAL - 15% SL)...")
    load_dotenv()
    
    transport = BackpackTransport()
    
    # 1. Get Positions
    try:
        positions = transport.get_positions()
    except Exception as e:
        print(f" Erro ao buscar posições: {e}")
        return

    if not positions:
        print(" Nenhuma posição aberta para proteger.")
        return

    print(f" Encontradas {len(positions)} posições abertas.")

    for pos in positions:
        symbol = pos.get('symbol')
        side = pos.get('side')
        qty = float(pos.get('netQuantity', pos.get('quantity', 0)))
        entry_price = float(pos.get('entryPrice'))
        
        if qty == 0: continue
        
        # Determine logical side if API returns mixed data
        if not side:
            side = "Long" if qty > 0 else "Short"
        
        print(f"\n️  Protegendo {symbol} ({side}) | Entry: {entry_price}")
        
        # 2. Calculate SL Price
        if side == "Long":
            sl_price = entry_price * (1 - SL_PERCENT)
            sl_side = "Ask" # Sell
        else: # Short
            sl_price = entry_price * (1 + SL_PERCENT)
            sl_side = "Bid" # Buy

        # Precision Adjustments (Backpack specific)
        if "BTC" in symbol: sl_price = round(sl_price, 1)
        elif "ETH" in symbol: sl_price = round(sl_price, 2)
        elif "SOL" in symbol: sl_price = round(sl_price, 2)
        elif "BNB" in symbol: sl_price = round(sl_price, 1) # BNB precision fix
        elif "HYPE" in symbol: sl_price = round(sl_price, 3)
        else: sl_price = round(sl_price, 4)

        print(f"    Target SL: {sl_price} (Dist: {SL_PERCENT*100}%)")

        # 3. Check Existing Orders
        open_orders = transport.get_open_orders(symbol)
        existing_sl = None
        
        for o in open_orders:
            o_type = o.get('orderType')
            trigger = float(o.get('triggerPrice', 0)) if o.get('triggerPrice') else 0
            
            # Identify Stop Order
            if 'Stop' in o_type or (o_type == 'Market' and trigger > 0):
                existing_sl = o
                print(f"   ️  SL Existente encontrado: {trigger}")
                break
        
        # 4. Action
        if existing_sl:
            print(f"    Cancelando SL antigo para ajustar...")
            transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': existing_sl['id']})
            await asyncio.sleep(0.5)
        
        # Place New SL
        payload = {
            "symbol": symbol,
            "side": sl_side,
            "orderType": "Market", # Corrected: Use Market + triggerPrice for Stop Market
            "quantity": str(abs(qty)),
            "triggerPrice": str(sl_price),
            "triggerQuantity": str(abs(qty)) # Required by Backpack API
        }
        
        print(f"    Enviando Stop Market...")
        res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        
        if res:
            print(f"    SL DEFINIDO COM SUCESSO: {sl_price}")
        else:
            print(f"    ERRO AO DEFINIR SL: {res}")
            
        await asyncio.sleep(0.5) # Rate limit safe

    print("\n PROTOCOLO NIGHT GUARD CONCLUÍDO.")

if __name__ == "__main__":
    asyncio.run(main())
