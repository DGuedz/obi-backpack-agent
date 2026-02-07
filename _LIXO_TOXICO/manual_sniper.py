#!/usr/bin/env python3
"""
 Manual Sniper - Immediate Execution
Dispara uma ordem de teste imediata no mercado.
"""

import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from guard_rails import GuardRail

load_dotenv()

class ManualSniper:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.guard = GuardRail()
        
        self.symbol = "MET_USDC_PERP"
        self.leverage = 5 # Menor alavancagem para Altcoin volátil
        self.cost_usdc = 50.0

    def fire(self):
        print(f" SNIPER MANUAL: Preparando disparo em {self.symbol}...")
        
        # 1. Obter Preço
        ticker = self.data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        print(f"   Preço Atual: ${price}")
        
        # 2. Calcular Tamanho
        notional = self.cost_usdc * self.leverage
        # MET tem preço baixo, quantidade alta. Arredondar para inteiro ou 1 casa.
        quantity = int(notional / price) 
        print(f"   Size: {quantity} MET (${notional} Notional)")
        
        # ️ GUARDRAIL CHECK
        # Verifica se o Spread e as Taxas permitem o tiro
        # Projetamos um lucro mínimo de 1% para valer a pena o risco Taker
        is_viable, reason = self.guard.check_trade_viability(
            self.symbol, "Bid", price, quantity, is_maker=False, projected_profit_pct=0.01
        )
        
        if not is_viable:
            print(f" TIRO BLOQUEADO PELO GUARDRAIL: {reason}")
            print("   ️ O mercado não está favorável para execução a mercado.")
            return

        # 3. Executar (Market Buy)
        print("    Guardrail Aprovado. Disparando...")
        order = self.trade.execute_order(
            symbol=self.symbol,
            side="Bid",
            order_type="Market",
            quantity=quantity,
            price=0 # Market não usa preço
        )
        
        if order and order.get('id'):
            print(f"    ALVO ATINGIDO! Ordem ID: {order['id']}")
            print("    Verifique seu PnL no App agora.")
        else:
            print("    Falha no disparo.")

if __name__ == "__main__":
    sniper = ManualSniper()
    sniper.fire()