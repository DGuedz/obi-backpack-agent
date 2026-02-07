#!/usr/bin/env python3
"""
 PENTAGON STRIKE
Executa 5 ordens Limit Sniper simultâneas.
Diversificação de Risco e Entrada Maker.
"""

import os
import time
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

# Configuração
MARGIN = 20.0
LEVERAGE = 5
SIZE_USDC = MARGIN * LEVERAGE # $100

# Alvos (Preços Sniper - Abaixo do Mercado Atual)
TARGETS = [
    {"symbol": "ETH_USDC_PERP", "price": 3285.00},
    {"symbol": "WIF_USDC_PERP", "price": 0.3750},
    {"symbol": "JUP_USDC_PERP", "price": 0.2200},
    {"symbol": "SOL_USDC_PERP", "price": 142.50}, # Reforço
    # SOL $143.10 já foi armado manualmente
]

def execute_strike():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    
    print(f"\n PENTAGON STRIKE: Armando {len(TARGETS)} Snipers...")
    print(f"   Size por Ordem: ${SIZE_USDC} (5x Lev)")
    print("-" * 50)
    
    for target in TARGETS:
        symbol = target['symbol']
        price = target['price']
        quantity = round(SIZE_USDC / price, 2)
        
        # Ajustes de precisão de quantidade
        if "WIF" in symbol or "JUP" in symbol: quantity = int(quantity)
        
        print(f"    {symbol}: Buy Limit @ ${price} (Qty: {quantity})")
        
        res = trade.execute_order(
            symbol, "Bid", price, quantity, "Limit", post_only=True
        )
        
        if res and res.get('id'):
            print(f"       Ordem Armada! ID: {res['id']}")
        else:
            print(f"       Falha: {res}")
            
        time.sleep(0.2) # Evitar Rate Limit
        
    print("-" * 50)
    print(" Todas as armadilhas posicionadas. Aguardando a caça.")

if __name__ == "__main__":
    execute_strike()