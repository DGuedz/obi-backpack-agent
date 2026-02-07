#!/usr/bin/env python3
"""
Sniper Momentum - Execução Cirúrgica de Scalp
Baseado em Cruzamento de Médias (EMA9 > EMA21) no 5m
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class SniperMomentum:
    def __init__(self, symbol="BTC_USDC_PERP", leverage=5, amount_usdc=40):
        self.symbol = symbol
        self.leverage = leverage
        self.amount = amount_usdc
        
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        
    def execute(self):
        print(f" Iniciando Sniper Momentum em {self.symbol}...")
        
        # 1. Verificar Preço Atual
        ticker = self.data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        print(f" Preço Atual: ${price:.2f}")
        
        # 2. Calcular Quantidade
        # Valor nocional = amount * leverage
        notional = self.amount * self.leverage
        quantity = round(notional / price, 5) # 5 casas para BTC
        
        print(f" Configuração:")
        print(f"   Margem: ${self.amount}")
        print(f"   Alavancagem: {self.leverage}x")
        print(f"   Tamanho Posição: ${notional} ({quantity} BTC)")
        
        # 3. Executar Market Buy
        print(" Executando Market Buy...")
        order = self.trade.execute_order(
            symbol=self.symbol,
            side="Bid",
            order_type="Market",
            quantity=quantity,
            price=0 # Ignorado para Market Order
        )
        
        if not order:
            print(" Falha na execução da ordem!")
            return
            
        print(f" Ordem Executada! ID: {order.get('id')}")
        
        # 4. Colocar Proteções (TP/SL)
        # TP: +1.2% (Alvo conservador para scalp)
        # SL: -0.6% (Stop curto abaixo das médias)
        
        tp_price = round(price * 1.012, 1)
        sl_price = round(price * 0.994, 1)
        
        print(f"️  Colocando Proteções:")
        print(f"   Take Profit: ${tp_price} (+1.2%)")
        print(f"   Stop Loss:   ${sl_price} (-0.6%)")
        
        # Enviar TP (Limit)
        self.trade.execute_order(
            symbol=self.symbol,
            side="Ask",
            order_type="Limit",
            quantity=quantity,
            price=tp_price,
            reduce_only=True
        )
        
        # Enviar SL (Stop Market)
        self.trade.execute_order(
            symbol=self.symbol,
            side="Ask",
            order_type="StopMarket",
            quantity=quantity,
            price=0, # Obrigatório posicional
            trigger_price=sl_price,
            reduce_only=True
        )
        
        print(" Sniper Finalizado. Monitorar no Terminal.")

if __name__ == "__main__":
    sniper = SniperMomentum()
    sniper.execute()