
import asyncio
import logging
import sys
import os
from typing import List, Dict
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport
from core.precision_guardian import PrecisionGuardian

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("ShieldDeployer")

async def deploy_shields():
    print("️ INICIANDO DEPLOY MANUAL DE ESCUDOS (PRECISION GUARDIAN)...")
    load_dotenv()
    transport = BackpackTransport()
    guardian = PrecisionGuardian(transport)
    
    # 1. Get Positions
    try:
        positions = transport.get_positions()
        if not positions:
            print(" Nenhuma posição aberta encontrada (ou erro API).")
            return
            
        print(f"DEBUG: First Pos Keys: {positions[0].keys()}")
        print(f"DEBUG: First Pos Raw: {positions[0]}")
            
        active_positions = []
        for p in positions:
            qty = float(p.get('quantity', 0))
            net_qty = float(p.get('netQuantity', 0))
            if qty != 0 or net_qty != 0:
                active_positions.append(p)
                
        print(f" Encontradas {len(active_positions)} posições ativas.")
        
    except Exception as e:
        print(f" Erro ao buscar posições: {e}")
        return

    # 2. Check and Protect
    for pos in active_positions:
        symbol = pos['symbol']
        # Use netQuantity!
        raw_qty = float(pos.get('netQuantity', 0))
        qty = abs(raw_qty)
        entry = float(pos['entryPrice'])
        side = "Long" if raw_qty > 0 else "Short"
        
        print(f"\n Verificando {symbol} ({side}) | Qty: {qty} | Entry: {entry}")
        
        # Get Orders
        orders = transport.get_open_orders(symbol)
        is_protected = False
        
        if orders:
            for o in orders:
                o_side = o.get('side')
                o_type = o.get('orderType')
                trigger = o.get('triggerPrice')
                
                required_side = "Ask" if side == "Long" else "Bid"
                
                if o_side == required_side and ("Stop" in o_type or (trigger and float(trigger) > 0)):
                    is_protected = True
                    print(f"    PROTEGIDO: Ordem {o.get('id')} ({o_type}) @ {trigger}")
                    break
        
        if not is_protected:
            print(f"    DESPROTEGIDO! Aplicando Stop Loss (3%)...")
            
            # Calc SL
            dist = 0.03
            if side == "Long":
                sl_price = entry * (1 - dist)
                sl_side = "Ask"
            else:
                sl_price = entry * (1 + dist)
                sl_side = "Bid"
                
            # Precision (Updated to use Guardian)
            sl_price_fmt = guardian.format_price(symbol, sl_price)
            qty_fmt = guardian.format_quantity(symbol, qty)
            
            payload = {
                "symbol": symbol,
                "side": sl_side,
                "orderType": "Market", # Changed from StopMarket to Market + Trigger
                "quantity": qty_fmt,
                "triggerPrice": sl_price_fmt,
                "triggerQuantity": qty_fmt # Added triggerQuantity
            }
            
            print(f"    Payload: {payload}")
            res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res:
                print(f"    ESCUDO ATIVADO!")
            else:
                print(f"    ERRO AO ATIVAR ESCUDO (API Error).")
                # FAIL-SAFE Logic for Manual Deploy
                print(f"   ️ TENTANDO FECHAR POSIÇÃO (FAIL-SAFE)...")
                transport.execute_order(symbol, "Market", "Sell" if side == "Long" else "Buy", qty_fmt)

if __name__ == "__main__":
    asyncio.run(deploy_shields())
