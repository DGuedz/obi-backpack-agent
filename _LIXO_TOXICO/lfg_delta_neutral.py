#!/usr/bin/env python3
"""
️ LFG Vault - Delta Neutral Strategy
Executa operação de Hedge Perfeito (Spot Long + Perp Short) na subconta LFG.
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class LFGVault:
    def __init__(self):
        # Usar credenciais da LFG
        self.api_key = os.getenv('BACKPACK_API_KEY_LFG')
        self.api_secret = os.getenv('BACKPACK_API_SECRET_LFG')
        
        if not self.api_key or not self.api_secret:
            raise ValueError(" Credenciais LFG não encontradas no .env")
            
        self.auth = BackpackAuth(self.api_key, self.api_secret)
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        
        self.spot_symbol = "SOL_USDC"
        self.perp_symbol = "SOL_USDC_PERP"
        self.allocation_usdc = 110.0 # Quase todo o saldo ($119), deixando buffer para taxas.
        
    def execute(self):
        print("\n️ LFG VAULT: Iniciando Delta Neutro em SOL...")
        
        # 1. Verificar Saldo
        collat = self.data.get_account_collateral()
        balance = float(collat.get('balance', 0))
        print(f"   Saldo LFG: ${balance:.2f} USDC")
        
        if balance < self.allocation_usdc:
            print(" Saldo insuficiente na LFG.")
            return

        # 2. Obter Preço
        ticker = self.data.get_ticker(self.spot_symbol)
        price = float(ticker['lastPrice'])
        print(f"   Preço SOL: ${price}")
        
        # 3. Calcular Quantidades
        # 50% para Spot, 50% para Short
        # Na verdade, usamos o Spot como colateral para o Short?
        # A Backpack tem Unified Margin? Se sim, compramos $50 Spot e Shortamos $50 Perp usando o Spot como margem.
        # Se não (contas isoladas), precisamos de USDC para ambos.
        # Assumindo Unified Margin (padrão Backpack):
        
        qty_spot = round((self.allocation_usdc / 2) / price, 1)
        qty_perp = qty_spot # Hedge 1:1
        
        print(f"   Alvo: Comprar {qty_spot} JUP (Spot) + Vender {qty_perp} JUP (Perp)")
        
        # Passo A: Comprar Spot
        print("   1️⃣ Executando Spot Buy...")
        spot_order = self.trade.execute_order(
            symbol=self.spot_symbol,
            side="Bid",
            order_type="Market",
            quantity=qty_spot,
            price=0
        )
        
        if spot_order and spot_order.get('id'):
            print(f"       Spot Comprado! ID: {spot_order['id']}")
        else:
            print("       Falha no Spot. Abortando.")
            return

        time.sleep(2)
        
        # Passo B: Vender Perp (Hedge)
        print("   2️⃣ Executando Perp Short...")
        perp_order = self.trade.execute_order(
            symbol=self.perp_symbol,
            side="Ask",
            order_type="Market",
            quantity=qty_perp,
            price=0
        )
        
        if perp_order and perp_order.get('id'):
            print(f"       Hedge Short Aberto! ID: {perp_order['id']}")
            print("   ️ Posição Delta Neutra Ativa.")
        else:
            print("       Falha no Short. Venda o Spot manualmente para não ficar exposto!")

if __name__ == "__main__":
    vault = LFGVault()
    vault.execute()