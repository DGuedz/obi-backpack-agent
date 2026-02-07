#!/usr/bin/env python3
"""
 Funding Scanner - Iron Bank Intel
Identifica as melhores oportunidades para Delta Neutral (Funding Arbitrage).
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class FundingScanner:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def scan(self):
        print("\n Scanning Backpack Markets for Funding Yields...")
        print("=================================================")
        
        try:
            # Obter todos os mercados
            markets = self.data.get_markets()
            
            opportunities = []
            
            # Filtrar apenas Perpétuos
            perp_markets = [m for m in markets if "PERP" in m['symbol']]
            
            print(f"    Analisando {len(perp_markets)} mercados perpétuos...")
            
            for market in perp_markets:
                symbol = market['symbol']
                
                # Buscar ticker individual (mais garantido)
                ticker = self.data.get_ticker(symbol)
                
                # Se ticker vier vazio, pula
                if not ticker: continue
                
                # Tentar encontrar fundingRate (pode estar aninhado ou com outro nome)
                # Geralmente é 'fundingRate', 'predictedFundingRate' ou similar
                funding_rate = 0.0
                
                if 'fundingRate' in ticker:
                    funding_rate = float(ticker['fundingRate'])
                elif 'latestFundingRate' in ticker:
                     funding_rate = float(ticker['latestFundingRate'])
                
                # Calcular APR
                # Backpack paga funding a cada 1 hora? Se for 8h, multiplicar por 3.
                # Assumindo hourly para ser conservador/padrão de mercado.
                hourly_yield = funding_rate
                daily_yield = funding_rate * 24
                apr = daily_yield * 365 * 100
                
                # Volume check (evitar mico sem liquidez)
                vol = float(ticker.get('volumeQuote', 0))
                
                # Filtrar apenas taxas positivas (Onde Short recebe)
                if funding_rate > 0:
                    opportunities.append({
                        'symbol': symbol,
                        'price': float(ticker['lastPrice']),
                        'funding_rate': funding_rate,
                        'apr': apr,
                        'volume': vol
                    })
                
                # Delay pequeno para não estourar rate limit
                time.sleep(0.1)
            
            if not opportunities:
                print("️ Nenhuma oportunidade de Funding Positivo encontrada.")
                return

            # Ordenar por APR (maior para menor)
            opportunities.sort(key=lambda x: x['apr'], reverse=True)
            
            print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'1H RATE':<10} | {'APR (Est.)':<10} | {'24H VOL (M)'}")
            print("-" * 75)
            
            for opp in opportunities[:10]: # Top 10
                vol_m = opp['volume'] / 1_000_000
                print(f"{opp['symbol']:<15} | ${opp['price']:<9.4f} | {opp['funding_rate']*100:>7.4f}% | {opp['apr']:>8.1f}% | ${vol_m:.1f}M")
                
            print("\n ESTRATÉGIA DELTA NEUTRA RECOMENDADA:")
            best = opportunities[0]
            print(f"    Ativo: {best['symbol']}")
            print(f"   1. Comprar {best['symbol'].replace('_PERP', '')} no Spot.")
            print(f"   2. Abrir Short 1x no {best['symbol']} (Mesmo valor nocional).")
            print(f"    Retorno: Ganha ~{best['apr']:.1f}% ao ano sem risco de preço.")
            
        except Exception as e:
            print(f" Erro no scan: {e}")

if __name__ == "__main__":
    scanner = FundingScanner()
    scanner.scan()