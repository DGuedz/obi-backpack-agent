#!/usr/bin/env python3
"""
Emergency Stop V2 - Tentativa com Limit + Trigger
"""
import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
trade = BackpackTrade(auth)

symbol = "BTC_USDC_PERP"
quantity = 0.00209
trigger = 94898.2
limit = 94850.0 

print(" Colocando Stop Loss V2 (Limit + Trigger)...")

res = trade.execute_order(
    symbol=symbol,
    side="Ask",
    order_type="Limit", # Usando Limit padrão
    quantity=quantity,
    price=limit,
    trigger_price=trigger, # Adicionando Trigger
    reduce_only=True
)

if res:
    print(f" Stop Colocado com Sucesso: ID {res.get('id')}")
else:
    print(" Falha V2.")