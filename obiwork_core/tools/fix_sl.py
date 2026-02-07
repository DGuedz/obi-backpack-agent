import os
import sys
import asyncio
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

async def fix_all_sl():
    load_dotenv()
    # Fix Auth initialization (Missing arguments error from previous context)
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    transport = BackpackTransport(auth)
    
    positions = transport.get_positions()
    if not positions:
        print(" Nenhuma posição aberta para ajustar.")
        return

    print(f" Encontradas {len(positions)} posições. Verificando Stops...")
    
    open_orders = transport.get_open_orders()
    
    for pos in positions:
        symbol = pos['symbol']
        qty = str(float(pos.get('quantity', pos.get('netQuantity', 0)))) # String for payload
        entry_price = float(pos.get('entryPrice', 0))
        side = pos.get('side', 'Long')
        
        # Check if Stop Exists
        has_stop = False
        if open_orders:
            for o in open_orders:
                if o['symbol'] == symbol and o['orderType'] in ['StopLimit', 'StopMarket']:
                    has_stop = True
                    break
        
        if not has_stop:
            print(f"️ {symbol}: SEM STOP LOSS! Criando agora...")
            
            # 1.5% Stop from Entry
            sl_pct = 0.015
            stop_price_val = entry_price * (1 - sl_pct) if side == "Long" else entry_price * (1 + sl_pct)
            
            # Format Price
            # Hardcoded precision for now or fetch? Fetch is better but let's be safe with 2 decimals for USDC pairs usually
            # Better: use string formatting relative to entry price precision
            stop_price = f"{stop_price_val:.2f}"
            
            close_side = "Ask" if side == "Long" else "Bid"
            
            # API FIX: Use "Market" with triggerPrice instead of "StopMarket" if API complains
            # Previous error: Expected input type "OrderTypeEnum", found "StopMarket".
            # This means "StopMarket" is not in the enum for V1 orderExecute endpoint?
            # Or maybe it's just "Market" but with a trigger?
            # Let's try "Market" + triggerPrice.
            
            payload = {
                "symbol": symbol,
                "side": close_side,
                "orderType": "Market", # Changed from StopMarket
                "quantity": qty.replace('-', ''),
                "triggerPrice": stop_price
            }
            # Remove triggerQuantity if using Market? Or keep it?
            # The previous error "Must specify both triggerPrice and triggerQuantity" was for StopMarket?
            # Let's try "Market" with triggerPrice. Usually that implies a Stop Market.
            # Wait, if I use "Market", triggerPrice might be ignored or cause error if not supported for Market type?
            # Let's check Backpack Docs logic:
            # "Stop Loss" is usually a Trigger Order.
            # If "StopMarket" enum is invalid, maybe it's "StopLoss" or "StopLossLimit"?
            # Or maybe we have to use a specific endpoint? No, usually same endpoint.
            # Let's try "Market" but pass triggerPrice.
            
            # Alternative: Maybe it's "StopLimit" but we want Market?
            # Let's try "Limit" with TimeInForce if needed? No, we need Stop.
            
            # ATTEMPT 4: Logic is circular.
            # 1. "StopMarket" invalid enum.
            # 2. "Market" requires triggerPrice AND triggerQuantity.
            # So we MUST use "Market" AND provide "triggerQuantity".
            
            payload = {
                "symbol": symbol,
                "side": close_side,
                "orderType": "Market",
                "quantity": qty.replace('-', ''),
                "triggerPrice": stop_price,
                "triggerQuantity": qty.replace('-', '')
            }

            
            print(f"   ️ Enviando Stop para {symbol} @ {stop_price}...")
            res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res and 'id' in res:
                print(f"    SL CRIADO: {symbol}")
            else:
                print(f"    ERRO AO CRIAR SL: {res}")
        else:
            print(f"    {symbol}: Stop OK.")

if __name__ == "__main__":
    asyncio.run(fix_all_sl())
