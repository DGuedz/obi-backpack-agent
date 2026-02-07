import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), 'strategies'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

async def check_and_update(symbol, target_price):
    load_dotenv()
    print(f"\n VERIFICANDO STATUS: {symbol}")
    
    transport = BackpackTransport()
    
    # 1. Verificar Posição
    print("1. Buscando Posições...")
    positions = transport.get_positions()
    target_pos = None
    
    for pos in positions:
        if pos['symbol'] == symbol:
            target_pos = pos
            break
            
    if not target_pos:
        print(f" Nenhuma posição aberta para {symbol}. Ordem de entrada pode não ter preenchido ainda.")
        # Check open orders just in case
    else:
        # Debug position structure
        print(f"DEBUG Position: {target_pos}")
        
        # Tentar pegar 'quantity' ou 'netQuantity' ou 'amount'
        qty = target_pos.get('quantity', target_pos.get('netQuantity', 0))
        entry = target_pos.get('entryPrice', 0)
        
        print(f" POSIÇÃO ENCONTRADA: {qty} {symbol} @ ${entry}")
        
        # 2. Verificar Ordens Abertas
        print("2. Buscando Ordens Abertas...")
        open_orders = transport.get_open_orders(symbol)
        
        tp_orders = []
        sl_orders = []
        
        for order in open_orders:
            oid = order['id']
            side = order['side']
            otype = order['orderType']
            price = order.get('price', 'Market')
            trigger = order.get('triggerPrice', 'N/A')
            
            print(f"   -> Ordem {oid}: {side} {otype} @ {price} (Trigger: {trigger})")
            
            # Identificar TP (Sell Orders que não são SL)
            # Geralmente SL tem triggerPrice < Entry (para Long)
            # TP tem triggerPrice > Entry ou é Limit Sell > Entry
            
            if side == "Ask": # Sell
                is_sl = False
                
                # Criterio: Se Trigger Price existe e é MENOR que entry, é SL.
                # Se Trigger Price existe e é MAIOR que entry, é TP.
                # Se não tem Trigger, é Limit Sell (Target).
                
                if trigger != 'N/A' and trigger is not None:
                     if float(trigger) < float(entry):
                        is_sl = True
                
                if is_sl:
                    sl_orders.append(order)
                    print(f"      [STOP LOSS - MANTER] Trigger {trigger} < Entry {entry}")
                else:
                    tp_orders.append(order)
                    print(f"      [ALVO/TP - CANCELAR] Trigger {trigger} > Entry {entry}")

        # 3. Cancelar TPs Antigos
        if tp_orders:
            print(f"3. Cancelando {len(tp_orders)} ordens de TP...")
            for order in tp_orders:
                res = transport.cancel_order(symbol, order['id'])
                print(f"   -> Cancelado {order['id']}: {res}")
        else:
            print("3. Nenhuma ordem de TP encontrada para cancelar.")
            
        # 4. Colocar Nova Ordem Limit
        print(f"4. Colocando Nova Ordem Limit Sell @ {target_price}...")
        
        # Garantir que a quantidade é a da posição
        # Mas cuidado se já houver vendas parciais (não é o caso agora)
        
        payload = {
            "symbol": symbol,
            "side": "Ask", # Sell
            "orderType": "Limit",
            "quantity": str(qty),
            "price": str(target_price),
            "postOnly": True
        }
        
        res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        if res and 'id' in res:
            print(f" NOVO ALVO DEFINIDO: Venda {qty} @ {target_price} (ID: {res['id']})")
        else:
            print(f" Erro ao criar nova ordem: {res}")

if __name__ == "__main__":
    asyncio.run(check_and_update("ETH_USDC_PERP", 2999))
