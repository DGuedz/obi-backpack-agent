#!/usr/bin/env python3
"""
 PROFIT CALCULATOR - PROJEÇÃO DE RETORNO
Calcula o lucro potencial das operações abertas (TP Hit) e o impacto no capital.
"""

import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

def calculate_profit():
    print(" CALCULADORA DE POTENCIAL DE RETORNO")
    print("========================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    active_positions = [p for p in positions if float(p['netQuantity']) != 0]
    
    total_potential_profit = 0.0
    total_risk = 0.0
    
    current_capital = 463.0 # Estimado
    
    for pos in active_positions:
        symbol = pos['symbol']
        qty = float(pos['netQuantity'])
        entry = float(pos['entryPrice'])
        side = "Long" if qty > 0 else "Short"
        
        # Encontrar TP
        tp_price = 0.0
        sl_price = 0.0
        
        sym_orders = [o for o in orders if o['symbol'] == symbol]
        for o in sym_orders:
            # TP
            if o['orderType'] == 'Limit' and o.get('reduceOnly') and o['side'] != side:
                tp_price = float(o['price'])
            # SL
            if (o['orderType'] == 'StopMarket' or o.get('triggerPrice')) and o['side'] != side:
                sl_price = float(o.get('triggerPrice', 0))

        if tp_price > 0:
            profit = abs(tp_price - entry) * abs(qty)
            total_potential_profit += profit
            roi = (profit / (abs(qty) * entry / 5)) * 100 # ROI sobre margem (5x)
            
            print(f" {symbol}:")
            print(f"   Entrada: ${entry:.4f} -> TP: ${tp_price:.4f}")
            print(f"    Lucro Projetado: +${profit:.2f} (ROI: {roi:.1f}%)")
        else:
            print(f" {symbol}: Sem TP definido.")
            
        if sl_price > 0:
            loss = abs(entry - sl_price) * abs(qty)
            total_risk += loss
            
        print("-" * 40)
        
    # Adicionar projeção BONK se ordem pegar
    # Assumindo $50 margem x 5 = $250 size. 4% TP.
    # Lucro = $250 * 0.04 = $10.00
    print(" PROJEÇÃO BONK (Se pegar ordem):")
    bonk_profit = 10.00
    print(f"    Lucro Projetado: +${bonk_profit:.2f}")
    total_potential_profit += bonk_profit
    print("-" * 40)

    print("========================================")
    print(f" LUCRO TOTAL PROJETADO: ${total_potential_profit:.2f}")
    print(f" RISCO TOTAL (Stop Loss): -${total_risk:.2f}")
    print(f" CAPITAL FINAL ESTIMADO: ${current_capital + total_potential_profit:.2f}")
    
    meta_pct = ((current_capital + total_potential_profit) / 500.0) * 100
    print(f" Progresso da Meta ($500): {meta_pct:.1f}%")

if __name__ == "__main__":
    calculate_profit()
