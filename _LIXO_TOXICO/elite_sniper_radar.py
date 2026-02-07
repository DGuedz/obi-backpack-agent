#!/usr/bin/env python3
"""
 ELITE SNIPER RADAR
Objetivo: Escanear oportunidades de Alta Probabilidade para o Setup Blood War ($100 | 10x).
Critérios:
1. Volatilidade Suficiente (ATR)
2. Tendência Clara (EMA + RSI)
3. Gatilho de Entrada (Pullback ou Breakout)
"""

import os
import time
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from market_intelligence import MarketIntelligence
from dotenv import load_dotenv

load_dotenv()

class EliteSniperRadar:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.mi = MarketIntelligence()
        
    def scan_market(self):
        print(" ELITE SNIPER RADAR: Escaneando o campo de batalha...")
        
        # 1. Obter Lista de Ativos (Perps)
        tickers = self.data.get_tickers()
        perps = [t for t in tickers if 'PERP' in t['symbol']]
        
        candidates = []
        
        for t in perps:
            symbol = t['symbol']
            price = float(t['lastPrice'])
            volume = float(t.get('quoteVolume', 0))
            
            # Filtro de Liquidez Mínima ($5M)
            if volume < 5_000_000: continue
            
            # 2. Análise Técnica Rápida
            # Precisamos de Klines para RSI e EMA
            klines = self.data.get_klines(symbol, "15m", limit=50)
            if not klines: continue
            
            closes = [float(k['close']) for k in klines]
            rsi = self.mi.calculate_rsi(closes)
            
            # EMA 20 (Tendência Curta)
            ema_20 = sum(closes[-20:]) / 20 # Média simples como proxy rápido
            
            # 3. Setup Blood War (Bollinger + RSI Confluence)
            # Requisito: Setup de 10x pede alta probabilidade
            
            # Calcular Bollinger Bands (usando método do MI)
            bb_upper, bb_mid, bb_lower = self.mi.calculate_bollinger_bands(closes)
            
            score = 0
            setup_type = "NEUTRAL"
            
            if bb_lower == 0: continue # Dados insuficientes
            
            # Setup LONG: Toque na Banda Inferior + RSI < 40
            if price <= bb_lower * 1.002 and rsi < 45:
                score += 3
                setup_type = "BOLLINGER DIP (LONG)"
                
            # Setup SHORT: Toque na Banda Superior + RSI > 60
            elif price >= bb_upper * 0.998 and rsi > 55:
                score += 3
                setup_type = "BOLLINGER TOP (SHORT)"
            
            # Setup BREAKOUT (Momentum)
            elif rsi > 65 and volume > 10_000_000:
                 score += 2
                 setup_type = "MOMENTUM BREAKOUT (LONG)"
            
            if score >= 2:
                candidates.append({
                    "symbol": symbol,
                    "price": price,
                    "rsi": rsi,
                    "volume": volume,
                    "setup": setup_type,
                    "score": score
                })
        
        # Ordenar por Score (Qualidade) depois por Volume
        candidates.sort(key=lambda x: (x['score'], x['volume']), reverse=True)
        
        print(f"\n ALVOS IDENTIFICADOS ({len(candidates)}):")
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'RSI':<6} | {'SETUP':<25} | {'VOLUME'}")
        print("-" * 75)
        
        for c in candidates[:5]: # Top 5
            vol_fmt = f"${c['volume']/1000000:.1f}M"
            print(f"{c['symbol']:<15} | ${c['price']:<9.2f} | {c['rsi']:<6.1f} | {c['setup']:<25} | {vol_fmt}")
            
        return candidates[:1] # Retorna o melhor alvo

if __name__ == "__main__":
    radar = EliteSniperRadar()
    radar.scan_market()
