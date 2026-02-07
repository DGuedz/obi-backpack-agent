#!/usr/bin/env python3
"""
Scalp Analyzer - Diagnóstico Rápido de Setup
Analisa BTC_USDC_PERP em 5m para confirmar Rebound/Momentum
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class ScalpAnalyzer:
    def __init__(self, symbol="BTC_USDC_PERP"):
        self.symbol = symbol
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
    def calculate_ema(self, prices, period):
        """Calcula EMA simples"""
        if len(prices) < period:
            return 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # SMA inicial
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
            
        return ema
        
    def calculate_rsi(self, prices, period=14):
        """Calcula RSI"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
                
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def analyze(self):
        print(f" Analisando {self.symbol} (5m)...")
        
        try:
            # Pegar últimas 50 velas de 5m
            klines = self.data.get_klines(self.symbol, "5m", limit=50)
            
            # Debug: Verificar estrutura
            if klines and len(klines) > 0:
                # print(f"DEBUG: Primeira vela: {klines[0]}")
                pass
            else:
                print(f" Sem dados de klines ou formato inválido: {klines}")
                return

            # Tentar extrair closes com proteção
            try:
                # Klines format: list of dicts {'close': '...', 'open': '...', ...}
                closes = [float(k['close']) for k in klines]
            except Exception as e:
                print(f" Erro ao processar klines: {e}")
                print(f"Dados recebidos: {klines[:2]}") # Mostrar primeiros 2
                return
                
            current_price = closes[-1]
            
            # Indicadores
            rsi = self.calculate_rsi(closes)
            ema9 = self.calculate_ema(closes, 9)
            ema21 = self.calculate_ema(closes, 21)
            
            print(f" Preço Atual: ${current_price:.2f}")
            print(f" RSI (14): {rsi:.2f}")
            print(f" EMA(9): ${ema9:.2f}")
            print(f" EMA(21): ${ema21:.2f}")
            
            # Diagnóstico
            trend = "BULLISH 🟢" if ema9 > ema21 else "BEARISH "
            momentum = "ALTA" if rsi > 50 else "BAIXA"
            
            print(f"\n Veredito Técnico:")
            print(f"   Tendência Curta: {trend}")
            print(f"   Momentum: {momentum}")
            
            if ema9 > ema21 and rsi > 45 and rsi < 70:
                print("    SETUP CONFIRMADO: Rebound em andamento!")
                print("    Recomendação: SCALP LONG (Alvo: Bandas Superiores)")
            elif rsi < 30:
                print("   ️ SETUP: OVERSOLD (Aguardando repique)")
            else:
                print("   ️ SETUP: NEUTRO/INDEFINIDO")
                
        except Exception as e:
            print(f" Erro na análise: {e}")

if __name__ == "__main__":
    analyzer = ScalpAnalyzer()
    analyzer.analyze()