#!/usr/bin/env python3
"""
 HOT ASSETS ANALYZER
Foco: Volume, RSI e Funding para identificar os ativos "Quentes".
"""

import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from market_intelligence import MarketIntelligence
from dotenv import load_dotenv

load_dotenv()

def analyze_hot_assets():
    print(" HOT ASSETS ANALYZER: Iniciando varredura...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    mi = MarketIntelligence()
    
    # 1. Obter Top Tickers por Volume
    tickers = data.get_tickers()
    if not tickers:
        print(" Erro ao obter tickers.")
        return

    perps = [t for t in tickers if 'PERP' in t['symbol']]
    perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
    
    top_15 = perps[:15]
    
    print(f"\n{'SYMBOL':<15} | {'PRICE':<10} | {'VOLUME':<10} | {'RSI (15m)':<10} | {'FUNDING':<10} | {'STATUS'}")
    print("-" * 85)
    
    for t in top_15:
        symbol = t['symbol']
        price = float(t['lastPrice'])
        vol = float(t.get('quoteVolume', 0)) / 1_000_000 # Em Milhões
        funding = float(t.get('fundingRate', 0)) * 100 # Em %
        
        # Calcular RSI (Requer Klines)
        klines = data.get_klines(symbol, "15m", limit=20)
        if klines:
            closes = [float(k['close']) for k in klines]
            rsi = mi.calculate_rsi(closes)
        else:
            rsi = 50.0
            
        # Status
        status = "NEUTRAL"
        if rsi > 70: status = "OVERBOUGHT "
        elif rsi < 30: status = "OVERSOLD 🟢"
        elif funding > 0.01: status = "HIGH FUNDING ️"
        
        print(f"{symbol:<15} | ${price:<9.2f} | ${vol:<9.1f}M | {rsi:<10.1f} | {funding:<9.4f}% | {status}")

if __name__ == "__main__":
    analyze_hot_assets()
