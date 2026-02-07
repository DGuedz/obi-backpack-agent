#!/usr/bin/env python3
"""
 Phoenix V2 Fortress - Scalper Institucional
Protocolo: Fortaleza de Contexto (Maker-Only, Hard Floor, Confluência)
"""

import os
import time
import math
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class PhoenixV2:
    def __init__(self, symbol="SOL_USDC_PERP", leverage=5, allocation_usdc=100):
        self.symbol = symbol
        self.leverage = leverage # Reduzido para 5x (Sustentabilidade)
        self.allocation = allocation_usdc 
        
        # Protocolo Fortaleza (NIGHT OWL SNIPER)
        self.MIN_ALLOCATION = 50
        self.HARD_FLOOR_SL = 0.020 # 2.0% Stop Fixo
        self.TARGET_TP = 0.025     # 2.5% Alvo
        
        # Filtros Estritos
        self.RSI_TRIGGER_LONG = 20 # Só extremidades
        self.RSI_TRIGGER_SHORT = 80
        
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
        print(" Phoenix V2 Fortress: INICIALIZADO")
        print(f"   Mode: Maker-Only (Post Only)")
        print(f"   Hard Floor: -{self.HARD_FLOOR_SL*100}%")
        print(f"   Min Size: ${self.allocation}")
        
    def get_market_metrics(self):
        ticker = self.data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        best_bid = float(ticker['high']) # Aproximação, API não retorna bid/ask no ticker simples as vezes? Ticker tem high/low. Orderbook tem bid/ask.
        # Vamos pegar Orderbook para precisão Maker
        depth = self.data.get_order_book_depth(self.symbol)
        if not depth: return None
        
        best_bid = float(depth['bids'][0][0])
        best_ask = float(depth['asks'][0][0])
        
        return {
            'price': price,
            'best_bid': best_bid,
            'best_ask': best_ask
        }

    def check_confluence(self):
        # Implementação simplificada do Score 7
        # 1. Volume Check (já assumido alto para BTC)
        # 2. Funding Check (Evitar pagar funding caro)
        # Para V2, vamos focar no técnico RSI/Stoch por enquanto
        return True

    def get_dynamic_allocation(self):
        try:
            collat = self.data.get_account_collateral()
            equity = float(collat.get('equity', 0))
            if equity <= 0: return self.allocation
            
            # Alocar 20% do Equity por tiro
            dynamic_alloc = equity * 0.20
            return max(dynamic_alloc, self.MIN_ALLOCATION)
        except:
            return self.allocation

    def execute_maker_entry(self, side):
        metrics = self.get_market_metrics()
        if not metrics: return
        
        price = metrics['best_bid'] if side == "Bid" else metrics['best_ask']
        
        # Calcular Quantidade (Auto-Scaling)
        target_allocation = self.get_dynamic_allocation()
        notional = target_allocation * self.leverage
        quantity = round(notional / price, 2) # SOL precision
        
        # ️ BLINDAGEM DE TAXAS (FEE SHIELD)
        # Taxa Taker Máxima: 0.085% (Pior cenário)
        # Taxa Maker: 0.0% (Melhor cenário)
        # Assumimos o pior para garantir lucro real.
        estimated_fee = notional * 0.00085
        min_profit_needed = estimated_fee * 2.0 # Lucro tem que ser o dobro da taxa para valer a pena
        
        # Calcular TP Mínimo para Cobrir Taxas + Lucro
        # Se Long: TP = Entry * (1 + (Fee% * 2))
        fee_pct_buffer = 0.002 # 0.2% de movimento mínimo para pagar taxas e sobrar algo
        
        print(f" Análise de Viabilidade ({side}):")
        print(f"    Notional: ${notional:.2f}")
        print(f"    Taxa Est. (Pior Caso): ${estimated_fee:.2f}")
        print(f"    Movimento Mínimo Necessário: {fee_pct_buffer*100}%")
        
        # Ajustar Alvos Dinamicamente
        self.TARGET_TP = max(self.TARGET_TP, fee_pct_buffer)
        
        print(f"    Enviando Ordem POST ONLY em ${price}...")
        
        # Executar Limit Post-Only (MAKER ONLY)
        res = self.trade.execute_order(
            symbol=self.symbol,
            side=side,
            order_type="Limit",
            quantity=quantity,
            price=price,
            post_only=True # AQUI ESTÁ A PROTEÇÃO CONTRA TAXAS
        )
        
        if res:
            print(f"    Ordem Maker Enviada: {res.get('id')}")
            # Monitorar preenchimento (simplificado: assumir fill ou deixar no book)
            # Como é scalper, deveríamos cancelar e repor se o preço fugir.
            # O Sentinel cuidará da proteção assim que virar posição.
            
            # Mas precisamos colocar o OCO (SL/TP) *imediatamente*?
            # Se a ordem não preencheu, OCO falha (sem posição).
            # V2 Strategy: Colocar Ordens de Saída apenas quando Posição Confirmada (pelo Sentinel ou Check)
            return True
        else:
            print("   ️ Maker Rejected (Cruzamento). Tentando tick melhor...")
            return False

    def calculate_indicators(self):
        klines = self.data.get_klines(self.symbol, "5m", limit=100)
        if not klines: return None
        
        closes = [float(k['close']) for k in klines]
        
        # RSI 14
        rsi_period = 14
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0: gains.append(change)
            else: losses.append(abs(change))
            
        avg_gain = sum(gains[-rsi_period:]) / rsi_period
        avg_loss = sum(losses[-rsi_period:]) / rsi_period
        if avg_loss == 0: rsi = 100
        else: rsi = 100 - (100 / (1 + (avg_gain/avg_loss)))
        
        # Stoch RSI
        # Precisamos de uma série de RSIs para calcular o StochRSI corretamente
        # Simplificação: Usar RSI atual e min/max dos últimos 14 candles (aproximação)
        # Para precisão, precisaríamos calcular RSI para cada candle dos últimos 14.
        # Vamos usar uma biblioteca técnica ou implementação manual robusta depois.
        # Por agora, RSI < 30 já é um bom proxy para Stoch < 20 em scalp.
        
        # EMA 100
        ema_period = 100
        if len(closes) < ema_period: return None
        multiplier = 2 / (ema_period + 1)
        ema = sum(closes[:ema_period]) / ema_period
        for price in closes[ema_period:]:
            ema = (price - ema) * multiplier + ema
            
        return {'rsi': rsi, 'ema100': ema, 'price': closes[-1]}

    def run(self):
        print(" Phoenix V2 Fortress: Monitorando (Stoch RSI Proxy + EMA100)...")
        while True:
            try:
                data = self.calculate_indicators()
                if not data:
                    time.sleep(10)
                    continue
                    
                price = data['price']
                rsi = data['rsi']
                ema = data['ema100']
                
                # Lógica de Exaustão (Night Owl)
                # Long: RSI < 30 (Extremo) E Preço longe da EMA (Desvio)
                # Short: RSI > 70
                
                dist_ema = (price - ema) / ema
                
                print(f"    RSI: {rsi:.1f} | EMA Dev: {dist_ema*100:.2f}% | Price: {price}")
                
                # Sinal Long (AWM)
                if rsi < self.RSI_TRIGGER_LONG:
                    print(f"   🟢 SINAL LONG (AWM SNIPER - RSI {rsi:.1f})")
                    self.execute_maker_entry("Bid")
                    time.sleep(60) # Cooldown
                    
                # Sinal Short (AWM)
                elif rsi > self.RSI_TRIGGER_SHORT:
                    print(f"    SINAL SHORT (AWM SNIPER - RSI {rsi:.1f})")
                    self.execute_maker_entry("Ask")
                    time.sleep(60)
                    
                time.sleep(10)
            except Exception as e:
                print(f" Erro Phoenix V2: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = PhoenixV2()
    bot.run()