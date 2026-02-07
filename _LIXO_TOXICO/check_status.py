#!/usr/bin/env python3
import os
import json
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from dotenv import load_dotenv

load_dotenv()

def check_status():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print(" Verificando Status da Conta...")
    
    # 1. Balances
    print("\n Saldos:")
    balances = data.get_balances()
    usdc = balances.get('USDC', {'available': 0, 'locked': 0})
    print(f"   USDC: {usdc['available']} (Locked: {usdc['locked']})")
    sol = balances.get('SOL', {'available': 0, 'locked': 0})
    print(f"   SOL:  {sol['available']} (Locked: {sol['locked']})")
    
    # 2. Open Positions
    print("\n Posições Abertas e PnL Estimado:")
    positions = data.get_positions()
    active_symbols = []
    
    total_unrealized_pnl = 0.0
    
    if positions:
        for p in positions:
            qty = float(p.get('netQuantity', 0))
            if qty != 0:
                symbol = p['symbol']
                entry = float(p.get('entryPrice', 0))
                side = "Long" if qty > 0 else "Short"
                
                # Buscar preço atual para PnL preciso
                ticker = data.get_ticker(symbol)
                current_price = float(ticker.get('lastPrice', entry))
                
                if side == "Long":
                    pnl = (current_price - entry) * abs(qty)
                else:
                    pnl = (entry - current_price) * abs(qty)
                
                total_unrealized_pnl += pnl
                
                print(f"    {symbol}: {qty} | Entry: ${entry:.4f} | Mark: ${current_price:.4f} | PnL: ${pnl:.2f}")
                active_symbols.append(symbol)
                
        print(f"\n    PnL Total Não Realizado: ${total_unrealized_pnl:.2f}")
        print(f"    Equity Estimado: ${usdc['available'] + usdc['locked'] + total_unrealized_pnl:.2f}")
    else:
        print("   (Nenhuma posição aberta)")
        
    # 3. Open Orders
    print("\n Ordens Abertas:")
    orders = data.get_open_orders()
    if orders:
        for o in orders:
            print(f"    {o['symbol']} {o['side']} {o['quantity']} @ {o.get('price')} ({o['orderType']})")
    else:
        print("   (Nenhuma ordem aberta)")
        
    return active_symbols

if __name__ == "__main__":
    check_status()
