#!/usr/bin/env python3
"""
 TWIN MIRROR ORCHESTRATOR
Estratégia de Farm de Volume Delta Neutro entre Subcontas.
"O que uma faz, a outra desfaz."
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class TwinMirror:
    def __init__(self):
        # Configurar Main
        self.auth_main = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade_main = BackpackTrade(self.auth_main)
        
        # Configurar LFG
        self.auth_lfg = BackpackAuth(os.getenv('BACKPACK_API_KEY_LFG'), os.getenv('BACKPACK_API_SECRET_LFG'))
        self.trade_lfg = BackpackTrade(self.auth_lfg)
        
        self.symbol = "SOL_USDC_PERP"
        self.size_usdc = 50.0 # Tamanho da ordem em cada ponta
        self.leverage = 5

    def check_lfg_access(self):
        try:
            # Tenta um comando leve para validar acesso
            data = BackpackData(self.auth_lfg)
            info = data.get_ticker(self.symbol)
            if info:
                print(" LFG Access: CONFIRMED")
                return True
        except Exception as e:
            print(f" LFG Access: DENIED ({e})")
            return False

    def execute_mirror(self):
        print(f"\n TWIN MIRROR: Iniciando Ciclo em {self.symbol}")
        
        # 1. Obter Preço
        data = BackpackData(self.auth_main)
        ticker = data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        quantity = round((self.size_usdc * self.leverage) / price, 2)
        
        print(f"   Preço: ${price} | Qty: {quantity} SOL | Notional: ${self.size_usdc * self.leverage}")
        
        # 2. Executar Perna 1 (Main - Long)
        print("    Executing MAIN: Long (Maker)...")
        # Coloca um pouco abaixo para garantir Maker
        bid_price = round(price * 0.9998, 2) 
        order_main = self.trade_main.execute_order(
            self.symbol, "Bid", bid_price, quantity, "Limit", post_only=True
        )
        
        if not order_main or not order_main.get('id'):
            print("    Falha na Main. Abortando LFG.")
            return

        print(f"    Main Order ID: {order_main['id']}")
        
        # 3. Executar Perna 2 (LFG - Short)
        print("    Executing LFG: Short (Maker)...")
        # Coloca um pouco acima para garantir Maker
        ask_price = round(price * 1.0002, 2)
        order_lfg = self.trade_lfg.execute_order(
            self.symbol, "Ask", ask_price, quantity, "Limit", post_only=True
        )
        
        if not order_lfg or not order_lfg.get('id'):
            print("   ️ Falha na LFG! Risco Direcional na Main! Cancelando Main...")
            self.trade_main.cancel_order(self.symbol, order_main['id'])
            return

        print(f"    LFG Order ID: {order_lfg['id']}")
        print("   ️ MIRROR ESTABELECIDO. Farmando Volume...")

if __name__ == "__main__":
    bot = TwinMirror()
    print("⏳ Aguardando propagação da chave LFG...")
    while True:
        if bot.check_lfg_access():
            bot.execute_mirror()
            break
        time.sleep(10)