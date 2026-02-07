#!/usr/bin/env python3
"""
 Volatility Radar - Target Acquisition
Identifica os ativos mais voláteis para operações Sniper/Grid.
"""

import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class VolatilityRadar:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def scan(self):
        print("\n Scanning for High Volatility Targets...")
        print("==========================================")
        
        try:
            # Tentar obter tickers (usando get_tickers se disponível, ou fallback)
            # Como vimos antes que get_tickers pode falhar, vamos usar get_markets e iterar
            markets = self.data.get_markets()
            
            targets = []
            
            # Filtrar Perpétuos
            perp_markets = [m for m in markets if "PERP" in m['symbol']]
            print(f"    Analisando {len(perp_markets)} mercados...")
            
            for market in perp_markets:
                symbol = market['symbol']
                ticker = self.data.get_ticker(symbol)
                
                if ticker and 'priceChangePercent' in ticker:
                    change = float(ticker['priceChangePercent'])
                    price = float(ticker['lastPrice'])
                    vol = float(ticker.get('volumeQuote', 0)) / 1_000_000 # Em Milhões
                    
                    targets.append({
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'vol_m': vol
                    })
            
            # Ordenar por Variação Absoluta (Mais voláteis, seja up ou down)
            targets.sort(key=lambda x: abs(x['change']), reverse=True)
            
            print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'24H CHG':<10} | {'VOL (M)'}")
            print("-" * 60)
            
            for t in targets[:8]:
                color = "🟢" if t['change'] > 0 else ""
                print(f"{color} {t['symbol']:<13} | ${t['price']:<9.4f} | {t['change']:>7.2f}% | ${t['vol_m']:.1f}M")
                
            print("\n RECOMENDAÇÃO TÁTICA:")
            best = targets[0]
            print(f"    Ativo mais quente: {best['symbol']} ({best['change']}%)")
            if abs(best['change']) > 10:
                print("   ️ Atenção: Alta Volatilidade. Use Weaver Grid (0.5% spacing) ou Phoenix V2.")
            else:
                print("    Mercado calmo. Phoenix V2 é mais seguro.")

        except Exception as e:
            print(f" Erro no radar: {e}")

if __name__ == "__main__":
    radar = VolatilityRadar()
    radar.scan()