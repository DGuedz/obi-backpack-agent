#!/usr/bin/env python3
"""
 MARKET INTELLIGENCE (TCP)
O Cérebro Central. Analisa Funding, OI, Book e Tendência.
Só autoriza operações com Alta Probabilidade Matemática.
"""

import os
import time
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

class MarketIntelligence:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1: return 50
        deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
        gains = [d for d in deltas if d > 0]
        losses = [abs(d) for d in deltas if d < 0]
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calcula Bollinger Bands (Upper, Middle, Lower)"""
        if len(prices) < period: return 0, 0, 0
        
        # SMA
        sma = sum(prices[-period:]) / period
        
        # Standard Deviation
        variance = sum([((x - sma) ** 2) for x in prices[-period:]]) / period
        std = variance ** 0.5
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower

    def analyze_multi_timeframe(self, symbol="SOL_USDC_PERP"):
        """
        Analisa confluência em múltiplos timeframes (5m, 1h, 4h, 6h).
        Retorna score consolidado.
        """
        timeframes = ["5m", "1h", "4h", "6h"]
        analyses = {}
        total_score = 0
        
        print(f"    Analisando Multi-Timeframe para {symbol}...")
        
        for tf in timeframes:
            # Reutiliza analyze_market_regime para cada TF
            # Nota: analyze_market_regime agora retorna dict completo
            data = self.analyze_market_regime(symbol, interval=tf)
            if data:
                analyses[tf] = data
                rsi = data['rsi']
                bb_lower = data['bb_lower']
                price = data['price']
                
                # Pontuação por TF
                tf_score = 0
                
                # RSI Logic
                if rsi < 40: tf_score += 1 # Oversold Bias
                if rsi > 60: tf_score += 1 # Trend Strength (Breakout)
                
                # Bollinger Logic (Bear Trap / Liquidity Hunt)
                if bb_lower > 0 and price <= bb_lower * 1.005: # Tocou banda inferior
                    tf_score += 2
                    print(f"      {tf}: Toque na Banda Inferior (Liquidez)!")
                
                total_score += tf_score
                print(f"     Checking {tf}: RSI={rsi:.1f} | Score={tf_score}")
                
        return analyses, total_score

    def analyze_market_regime(self, symbol="SOL_USDC_PERP", interval="15m"):
        """
        Retorna: regime, risk, rsi, advice, bb_lower, bb_upper
        """
        try:
            # 1. Dados de Mercado (Ticker)
            ticker = self.data.get_ticker(symbol)
            price = float(ticker['lastPrice'])
            funding = float(ticker.get('fundingRate', 0))
            
            # 2. Dados Históricos (Klines adaptáveis para Scalp)
            klines = self.data.get_klines(symbol, interval, limit=30) # Aumentado para BB (min 20)
            if klines:
                closes = [float(k['close']) for k in klines]
                rsi = self.calculate_rsi(closes)
                bb_upper, bb_mid, bb_lower = self.calculate_bollinger_bands(closes)
            else:
                rsi = 50 
                bb_upper, bb_mid, bb_lower = 0, 0, 0

            # 3. Funding Analysis
            funding_bias = "NEUTRAL"
            if funding > 0.015: funding_bias = "BEARISH_SQUEEZE"
            elif funding < -0.015: funding_bias = "BULLISH_SQUEEZE"
            
            # 4. Order Book Imbalance
            depth = self.data.get_depth(symbol)
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            
            bid_vol = sum([float(b[1]) for b in bids[:10]])
            ask_vol = sum([float(a[1]) for a in asks[:10]])
            
            if bid_vol + ask_vol > 0:
                imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol)
            else:
                imbalance = 0
            
            # 5. Volatilidade (Spread)
            best_ask = float(ticker.get('bestAsk', 0) or ticker.get('best_ask', 0) or ticker.get('ask', price * 1.0005))
            best_bid = float(ticker.get('bestBid', 0) or ticker.get('best_bid', 0) or ticker.get('bid', price * 0.9995))
            spread = (best_ask - best_bid) / best_bid
            
            # 6. Volume (Liquidez para Scalp)
            volume = float(ticker.get('quoteVolume', 0)) # Volume em USDC

            # DECISÃO FINAL (Score de Confluência)
            score = 0
            
            # Bollinger Bands Analysis
            bb_bias = "NEUTRAL"
            if bb_lower > 0:
                if price <= bb_lower * 1.002: # Tocou ou furou banda inferior (0.2% buffer)
                    score += 2
                    bb_bias = "OVERSOLD_BB"
                elif price >= bb_upper * 0.998: # Tocou ou furou banda superior
                    score -= 2
                    bb_bias = "OVERBOUGHT_BB"

            # RSI Confluence (Ajuste Fino: Reação Rápida)
            if rsi < 35: score += 2 # Oversold Forte
            if rsi > 65: score -= 2 # Overbought Forte
            if rsi < 45 and rsi > 35: score += 1 # Zona de Compra Moderada (Uptrend Pullback)
            if rsi > 55 and rsi < 65: score -= 1 # Zona de Venda Moderada (Downtrend Pullback)

            # Imbalance Confluence
            if imbalance > 0.15: score += 1
            if imbalance < -0.15: score -= 1
            
            # Funding (Smart Money Flow)
            if funding_bias == "BEARISH_SQUEEZE": score -= 1 # Muita gente pagando short
            if funding_bias == "BULLISH_SQUEEZE": score += 1 # Muita gente pagando long (Cuidado, pode ser topo, mas pra scalp é força)
            
            # Definir Regime
            regime = "NEUTRAL"
            if score >= 2: regime = "OVERSOLD_BOUNCE" # Chance de repique de alta
            elif score <= -2: regime = "OVERBOUGHT_DUMP" # Chance de correção
            
            # Risk Adjusted: Spread Tolerável até 0.15% em momentos de oportunidade
            risk = "LOW"
            if spread > 0.0015 or abs(funding) > 0.02: risk = "HIGH"
            
            return {
                "regime": regime,
                "score": score,
                "rsi": rsi,
                "price": price,
                "funding": funding,
                "spread": spread,
                "bb_lower": bb_lower,
                "bb_upper": bb_upper,
                "bb_mid": bb_mid
            }
        except Exception as e:
            print(f" Erro na análise de regime: {e}")
            return None

if __name__ == "__main__":
    mi = MarketIntelligence()
    print(mi.analyze_market_regime())