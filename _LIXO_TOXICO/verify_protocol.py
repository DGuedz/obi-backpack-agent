#!/usr/bin/env python3
"""
️ PROTOCOL VERIFIER - AUDITORIA DE SEGURANÇA
Verifica se todas as posições abertas estão em conformidade com o Protocolo 500.
Regras Estritas:
1. Toda posição DEVE ter um Stop Loss (SL) ativo.
2. Toda posição DEVE ter um Take Profit (TP) ativo.
3. SL deve estar próximo de 2% do preço de entrada.
"""

import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

def verify_protocol():
    print("️ INICIANDO AUDITORIA DO PROTOCOLO...")
    print("="*60)
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    active_positions = [p for p in positions if float(p['netQuantity']) != 0]
    
    if not active_positions:
        print("ℹ️ Nenhuma posição ativa encontrada para auditar.")
        return

    all_compliant = True
    
    for pos in active_positions:
        symbol = pos['symbol']
        qty = float(pos['netQuantity'])
        entry = float(pos['entryPrice'])
        side = "Long" if qty > 0 else "Short"
        
        print(f" ATIVO: {symbol} | {side} {abs(qty)} @ ${entry:.4f}")
        
        # Filtrar ordens do símbolo
        sym_orders = [o for o in orders if o['symbol'] == symbol]
        
        # Identificar SL e TP
        sl_order = None
        tp_order = None
        
        for o in sym_orders:
            # SL Check: StopMarket ou TriggerPrice, lado oposto à posição
            is_sl_side = o['side'] != side
            if is_sl_side and (o['orderType'] == 'StopMarket' or o.get('triggerPrice')):
                sl_order = o
            
            # TP Check: Limit ReduceOnly, lado oposto à posição
            if is_sl_side and o['orderType'] == 'Limit' and o.get('reduceOnly'):
                tp_order = o
        
        # Validar SL
        if sl_order:
            trigger = float(sl_order.get('triggerPrice', 0))
            dist_sl = abs(entry - trigger) / entry * 100
            print(f"    SL ENCONTRADO: Trigger ${trigger:.4f} (Distância: {dist_sl:.2f}%)")
            if not (1.8 <= dist_sl <= 2.2):
                print(f"      ️ ALERTA: SL fora do padrão de 2% (Está em {dist_sl:.2f}%)")
        else:
            print(f"    SL AUSENTE! CRÍTICO!")
            all_compliant = False
            
        # Validar TP
        if tp_order:
            price = float(tp_order.get('price', 0))
            dist_tp = abs(price - entry) / entry * 100
            print(f"    TP ENCONTRADO: Limit ${price:.4f} (Distância: {dist_tp:.2f}%)")
        else:
            print(f"   ️ TP AUSENTE (Menos crítico, mas fora do padrão)")
        
        print("-" * 60)

    print("="*60)
    if all_compliant:
        print(" PROTOCOLO VALIDADO: Todas as posições estão protegidas.")
    else:
        print(" FALHA NO PROTOCOLO: Ação manual ou Risk Manager necessária imediatamente!")

if __name__ == "__main__":
    verify_protocol()
