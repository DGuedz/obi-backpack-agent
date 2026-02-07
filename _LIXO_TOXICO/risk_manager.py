#!/usr/bin/env python3
"""
️ RISK MANAGER - GUARDIÃO AUTOMÁTICO
Monitora posições abertas e garante que TODAS tenham Stop Loss (SL) e Take Profit (TP).
Regra: SL 2% | TP 4% (Risco:Retorno 1:2)
"""

import os
import time
import math
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

def get_tick_size(data, symbol):
    try:
        filters = data.get_market_filters(symbol)
        return float(filters.get('tickSize', 0.01))
    except:
        return 0.01

def round_step(value, step):
    if step == 0: return value
    # Evitar erros de ponto flutuante
    precision = int(abs(math.log10(step)))
    if step < 1:
        return round(value, precision)
    return round(value - (value % step), precision)

def run_risk_manager():
    print("️ INICIANDO RISK MANAGER...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # Loop Único (pode ser transformado em while True se necessário)
    print(" Escaneando posições abertas...")
    
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    if not positions:
        print("   ℹ️ Nenhuma posição aberta encontrada.")
    
    for pos in positions:
        symbol = pos['symbol']
        qty = float(pos['netQuantity'])
        
        if qty == 0: continue
        
        entry = float(pos['entryPrice'])
        side = "Long" if qty > 0 else "Short"
        abs_qty = abs(qty)
        
        print(f"\n   🟢 POSIÇÃO DETECTADA: {symbol} | {side} {abs_qty} @ ${entry}")
        
        # Verificar ordens existentes
        has_sl = False
        has_tp = False
        
        symbol_orders = [o for o in orders if o['symbol'] == symbol]
        
        for o in symbol_orders:
            o_type = o.get('orderType')
            o_side = o.get('side')
            o_price = float(o.get('price', 0)) if o.get('price') else 0
            o_trigger = float(o.get('triggerPrice', 0)) if o.get('triggerPrice') else 0
            
            # Checar SL (StopMarket ou StopLimit contra a posição)
            # Long -> Sell SL (Trigger < Entry)
            if side == "Long" and o_side == "Ask":
                if o_type == "StopMarket": has_sl = True
                if o_type == "StopLimit" and o_trigger < entry: has_sl = True
            
            # Checar TP (Limit Sell > Entry)
            if side == "Long" and o_side == "Ask" and o_type == "Limit":
                if o_price > entry: has_tp = True

            # Short -> Buy SL (Trigger > Entry)
            if side == "Short" and o_side == "Bid":
                if o_type == "StopMarket": has_sl = True
                if o_type == "StopLimit" and o_trigger > entry: has_sl = True
                
            # Short TP (Limit Buy < Entry)
            if side == "Short" and o_side == "Bid" and o_type == "Limit":
                if o_price < entry: has_tp = True

        # Tick Size para arredondamento
        tick_size = get_tick_size(data, symbol)
        
        # Correção de Quantidade para BONK (Step Size 100)
        qty_to_trade = abs_qty
        if symbol == 'kBONK_USDC_PERP':
            qty_to_trade = int(abs_qty) # Garantir inteiro
            qty_to_trade = str(qty_to_trade) # API exige string
        
        # Lógica de Proteção
        if not has_sl:
            sl_dist = entry * 0.02 # 2%
            sl_price = entry - sl_dist if side == "Long" else entry + sl_dist
            sl_price = round_step(sl_price, tick_size)
            
            print(f"     ️ SL AUSENTE! Colocando Stop Market @ ${sl_price} (-2%)")
            
            # Tentar "Market" com triggerPrice (Padrão Backpack para Stop Market)
            
            # Payload específico para BONK se necessário
            payload = {
                "symbol": symbol,
                "side": "Ask" if side == "Long" else "Bid",
                "orderType": "Market",
                "triggerPrice": str(sl_price),
                "triggerQuantity": str(qty_to_trade), # Trigger Quantity obrigatorio
                "reduceOnly": True
            }
            
            # Executar via requests direto se for BONK para garantir formato
            if symbol == 'kBONK_USDC_PERP':
                import requests
                headers = auth.get_headers(instruction="orderExecute", params=payload)
                url = "https://api.backpack.exchange/api/v1/order"
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print(f"        SL BONK Criado! ID {response.json().get('id')}")
                else:
                    print(f"        Falha SL BONK: {response.text}")
            else:
                res = trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    price=None,
                    quantity=abs_qty,
                    order_type="Market", 
                    trigger_price=sl_price,
                    reduce_only=True
                )
                if res: print(f"        SL Criado: ID {res.get('id')}")
                else: print(f"        Falha ao criar SL.")
            
        else:
            print(f"      SL já configurado.")
            
        if not has_tp:
            tp_dist = entry * 0.04 # 4%
            tp_price = entry + tp_dist if side == "Long" else entry - tp_dist
            tp_price = round_step(tp_price, tick_size)
            
            print(f"     ️ TP AUSENTE! Colocando Limit @ ${tp_price} (+4%)")
            
            if symbol == 'kBONK_USDC_PERP':
                payload = {
                    "symbol": symbol,
                    "side": "Ask" if side == "Long" else "Bid",
                    "orderType": "Limit",
                    "price": str(tp_price),
                    "quantity": str(qty_to_trade),
                    "reduceOnly": True
                }
                import requests
                headers = auth.get_headers(instruction="orderExecute", params=payload)
                url = "https://api.backpack.exchange/api/v1/order"
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print(f"        TP BONK Criado! ID {response.json().get('id')}")
                else:
                    print(f"        Falha TP BONK: {response.text}")
            else:
                res = trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    price=tp_price,
                    quantity=abs_qty,
                    order_type="Limit",
                    reduce_only=True
                )
                if res: print(f"        TP Criado: ID {res.get('id')}")
                else: print(f"        Falha ao criar TP.")
            
        else:
             print(f"      TP já configurado.")

    print("\n️ RISK MANAGER CONCLUÍDO.")

if __name__ == "__main__":
    run_risk_manager()
