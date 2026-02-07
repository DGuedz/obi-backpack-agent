#!/usr/bin/env python3
"""
️ Iron Reserve - Spot Accumulator
Compra SOL no mercado Spot para hold ou colateral.
"""

import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class SpotBuyer:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.symbol = "SOL_USDC" # SPOT MARKET
        self.amount_usdc = 50.0

    def execute(self):
        print(f"\n️ IRON RESERVE: Comprando {self.symbol} (Spot)...")
        
        # 1. Obter Preço
        ticker = self.data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        print(f"   Preço Atual: ${price}")
        
        # 2. Calcular Quantidade (SOL)
        # Spot não tem alavancagem. $50 USDC = $50 SOL
        quantity = round(self.amount_usdc / price, 2)
        
        print(f"   Investimento: ${self.amount_usdc} USDC")
        print(f"   Quantidade: {quantity} SOL")
        
        # 3. Executar (Market Buy)
        # Nota: API Spot pode exigir quantidade mínima. 0.3 SOL deve passar.
        order = self.trade.execute_order(
            symbol=self.symbol,
            side="Bid",
            order_type="Market",
            quantity=quantity,
            price=0
        )
        
        if order and order.get('id'):
            print(f"    COMPRA SPOT REALIZADA! ID: {order['id']}")
            print("    O SOL agora faz parte do seu Colateral.")
        else:
            print("    Falha na compra Spot.")

if __name__ == "__main__":
    buyer = SpotBuyer()
    buyer.execute()