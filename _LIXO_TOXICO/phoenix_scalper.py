#!/usr/bin/env python3
"""
Phoenix Scalper - Estratégia de Momentum Complementar ao Weaver Grid
Foca em movimentos rápidos de 5-10% com risco controlado
"""

import os
import time
import json
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# Carregar variáveis de ambiente
load_dotenv()

class PhoenixScalper:
    def __init__(self, symbol="BTC_USDC_PERP", leverage=5, allocation_usdc=75):
        self.symbol = symbol
        self.leverage = leverage
        self.allocation = allocation_usdc
        
        # Inicializar autenticação e dados
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
        print(f" Phoenix Scalper Iniciado")
        print(f" Par: {self.symbol}")
        print(f"️  Alavancagem: {self.leverage}x")
        print(f" Alocação: ${self.allocation} USDC")
        print("-" * 50)
    
    def get_market_data(self):
        """Coleta dados de mercado em tempo real"""
        try:
            # Preço atual via ticker
            ticker = self.data.get_ticker(self.symbol)
            price = float(ticker['lastPrice'])
            
            # Dados de 5min para análise
            klines = self.data.get_klines(self.symbol, "5m", limit=20)
            
            # Volume médio das últimas 20 velas
            volumes = [float(k[5]) for k in klines]  # Volume é o índice 5
            avg_volume = sum(volumes) / len(volumes)
            current_volume = volumes[-1] if volumes else 0
            
            return {
                'price': price,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
            }
        except Exception as e:
            print(f" Erro ao coletar dados: {e}")
            return None
    
    def calculate_rsi(self, prices, period=14):
        """Calcula RSI simples"""
        if len(prices) < period + 1:
            return 50  # Neutro se não há dados suficientes
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_entry_signal(self, market_data):
        """Verifica condições de entrada"""
        if not market_data:
            return False
        
        # Coletar últimas 20 velas para RSI
        klines = self.data.get_klines(self.symbol, "5m", limit=20)
        prices = [float(k[4]) for k in klines]  # Preço de fechamento
        
        # Calcular RSI
        rsi = self.calculate_rsi(prices)
        
        # Condições de entrada
        oversold = rsi < 30
        volume_spike = market_data['volume_ratio'] > 2.0  # Volume 2x acima da média
        
        print(f" RSI: {rsi:.1f} | Volume: {market_data['volume_ratio']:.1f}x")
        
        return oversold and volume_spike
    
    def execute_trade(self, direction):
        """Executa trade com risco controlado"""
        try:
            price = self.data.get_price(self.symbol)
            
            # Calcular tamanho da posição
            position_size = (self.allocation * self.leverage) / price
            
            # Arredondar para quantidade permitida
            if "BTC" in self.symbol:
                quantity = round(position_size, 5)  # 5 casas decimais para BTC
            else:
                quantity = round(position_size, 2)  # 2 casas para outros
            
            print(f" Entrada {direction.upper()} detectada!")
            print(f" Preço: ${price:.2f}")
            print(f" Quantidade: {quantity}")
            print(f" Valor: ${self.allocation * self.leverage:.2f} (5x)")
            
            # Colocar ordem MARKET (para entrada rápida)
            order = self.data.place_order(
                symbol=self.symbol,
                side=direction,
                type="MARKET",
                quantity=quantity
            )
            
            print(f" Ordem executada: {order['id']}")
            
            # Colocar STOP LOSS e TAKE PROFIT imediatamente
            self.place_protection_orders(direction, price, quantity)
            
            return True
            
        except Exception as e:
            print(f" Erro na execução: {e}")
            return False
    
    def place_protection_orders(self, direction, entry_price, quantity):
        """Coloca ordens de proteção (OCO)"""
        try:
            if direction == "buy":
                # STOP LOSS: -2%
                stop_price = entry_price * 0.98
                # TAKE PROFIT: +5%
                take_profit_price = entry_price * 1.05
                
                # Colocar STOP LOSS
                sl_order = self.data.place_order(
                    symbol=self.symbol,
                    side="sell",
                    type="STOP_MARKET",
                    quantity=quantity,
                    stop_price=stop_price
                )
                
                # Colocar TAKE PROFIT
                tp_order = self.data.place_order(
                    symbol=self.symbol,
                    side="sell",
                    type="LIMIT",
                    quantity=quantity,
                    price=take_profit_price,
                    time_in_force="GTC"
                )
                
                print(f"️  Proteções colocadas:")
                print(f"   STOP: ${stop_price:.2f} (-2%)")
                print(f"   TP: ${take_profit_price:.2f} (+5%)")
                
            elif direction == "sell":
                # Lógica similar para short (ajustar preços)
                stop_price = entry_price * 1.02  # +2% para short
                take_profit_price = entry_price * 0.95  # -5% para short
                
                # Colocar STOP LOSS (buy para fechar short)
                sl_order = self.data.place_order(
                    symbol=self.symbol,
                    side="buy",
                    type="STOP_MARKET",
                    quantity=quantity,
                    stop_price=stop_price
                )
                
                # Colocar TAKE PROFIT (buy para fechar short)
                tp_order = self.data.place_order(
                    symbol=self.symbol,
                    side="buy",
                    type="LIMIT",
                    quantity=quantity,
                    price=take_profit_price,
                    time_in_force="GTC"
                )
                
                print(f"️  Proteções colocadas:")
                print(f"   STOP: ${stop_price:.2f} (+2%)")
                print(f"   TP: ${take_profit_price:.2f} (-5%)")
        
        except Exception as e:
            print(f" Erro nas proteções: {e}")
    
    def check_open_positions(self):
        """Verifica se já há posições abertas"""
        try:
            positions = self.data.get_positions()
            open_positions = [p for p in positions 
                            if p['symbol'] == self.symbol and float(p['size']) != 0]
            return len(open_positions) > 0
        except:
            return False
    
    def run(self):
        """Loop principal de trading"""
        print(" Phoenix Scalper ativo - Monitorando oportunidades...")
        
        while True:
            try:
                # Verificar se já tem posição aberta
                if self.check_open_positions():
                    print("⏸️  Posição aberta detectada - Aguardando fechamento...")
                    time.sleep(60)
                    continue
                
                # Coletar dados de mercado
                market_data = self.get_market_data()
                if not market_data:
                    time.sleep(30)
                    continue
                
                print(f" {self.symbol}: ${market_data['price']:.2f} "
                      f"| Volume: {market_data['volume_ratio']:.1f}x")
                
                # Verificar sinal de entrada
                if self.check_entry_signal(market_data):
                    # Entrar LONG (buy) quando oversold + volume spike
                    success = self.execute_trade("buy")
                    if success:
                        print(" Trade executado - Aguardando 1h para próximo sinal")
                        time.sleep(3600)  # Esperar 1h após entrada
                
                time.sleep(30)  # Verificar a cada 30 segundos
                
            except Exception as e:
                print(f" Erro no loop principal: {e}")
                time.sleep(60)

if __name__ == "__main__":
    # Inicializar scalper com configuração conservadora
    scalper = PhoenixScalper(
        symbol="BTC_USDC_PERP",  # Alta liquidez, baixo spread
        leverage=5,              # Risco moderado
        allocation_usdc=75       # 50% da margem livre
    )
    
    scalper.run()