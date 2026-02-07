import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

async def audit():
    load_dotenv()
    transport = BackpackTransport()
    
    symbol = "BTC_USDC_PERP"
    
    print(f"--- AUDITORIA DE ORDENS: {symbol} ---")
    
    # 1. Posições
    positions = await asyncio.to_thread(transport.get_positions)
    my_pos = next((p for p in positions if p['symbol'] == symbol), None)
    
    has_position = False
    if my_pos and float(my_pos['netQuantity']) != 0:
        has_position = True
        entry = float(my_pos['entryPrice'])
        qty = float(my_pos['netQuantity'])
        side = "LONG" if qty > 0 else "SHORT"
        print(f"POSIÇÃO ABERTA: {side} | Qty: {qty} | Entry: {entry}")
    else:
        print("SEM POSIÇÃO ABERTA.")

    # 2. Ordens Abertas
    orders = await asyncio.to_thread(transport.get_open_orders, symbol)
    
    if not orders:
        print("Nenhuma ordem aberta.")
        return

    print(f"\nEncontradas {len(orders)} ordens abertas:")
    
    orders_to_cancel = []
    
    # Obter preço atual (Mark Price) para referência
    # Usando get_ticker ou similar se disponível, ou estimando pelo order book
    # Vamos assumir que get_ticker não está exposto facilmente no transport síncrono wrapper, 
    # mas podemos ver o preço das ordens.
    
    for o in orders:
        o_id = o['id']
        o_side = o['side']
        o_price = float(o['price'])
        o_type = o['orderType']
        o_qty = float(o['quantity'])
        
        print(f"- [{o_id}] {o_type} {o_side} {o_qty} @ {o_price}")
        
        # Lógica de Limpeza
        # Se NÃO temos posição, todas as ordens abertas são 'tentativas' de entrada.
        # Se o usuário quer liberar margem, devemos cancelar entradas antigas/penduradas.
        if not has_position:
            print(f"  -> CANCELAR (Sem posição, liberando margem)")
            orders_to_cancel.append(o_id)
        else:
            # Temos posição.
            # Se a ordem for do mesmo lado da posição (ex: Long e ordem Buy), é aumento de posição.
            # Se for lado oposto (ex: Long e ordem Sell), é TP ou SL.
            pos_side = "Bid" if float(my_pos['netQuantity']) > 0 else "Ask" # Bid=Buy=Long? Não. side da ordem API é 'Bid'/'Ask' ou 'Buy'/'Sell'?
            # API Backpack retorna side: 'Bid' ou 'Ask'.
            # Posição Long (qty > 0). TP seria Sell (Ask). SL seria Sell (Ask).
            # Aumento seria Buy (Bid).
            
            is_reduce = False
            if float(my_pos['netQuantity']) > 0: # LONG
                if o_side == 'Ask': is_reduce = True
            else: # SHORT
                if o_side == 'Bid': is_reduce = True
            
            if not is_reduce:
                # É uma ordem de aumento de posição.
                # Se o usuário quer 'liberar margem', aumentar posição consome margem.
                print(f"  -> CANCELAR (Aumento de posição consome margem)")
                orders_to_cancel.append(o_id)
            else:
                print(f"  -> MANTER (TP/SL/Redução de posição)")

    if orders_to_cancel:
        print(f"\nCancelando {len(orders_to_cancel)} ordens...")
        for oid in orders_to_cancel:
            await asyncio.to_thread(transport.cancel_order, symbol, oid)
            print(f"Ordem {oid} cancelada.")
    else:
        print("\nNenhuma ordem para cancelar.")

if __name__ == "__main__":
    asyncio.run(audit())
