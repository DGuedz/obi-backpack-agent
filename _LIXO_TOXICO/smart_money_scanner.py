#!/usr/bin/env python3
"""
 SMART MONEY SCANNER
Objetivo: Rastrear o fluxo de capital ("Smart Money") na Backpack.
Métricas:
1. Volume Anormal (Interesse)
2. Funding Rate (Viés Institucional)
3. Liquidez/Spread (Onde as Baleias conseguem entrar)
"""

import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv
import time

load_dotenv()

class SmartMoneyScanner:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def scan(self):
        print(" Iniciando varredura de SMART MONEY...")
        
        # 1. Obter Tickers (Volume e Funding)
        tickers = self.data.get_tickers()
        if not tickers:
            print(" Falha ao obter tickers.")
            return

        # Filtrar apenas PERP (Futuros onde o Smart Money alavanca)
        perps = [t for t in tickers if 'PERP' in t['symbol']]
        
        print(f"    Analisando {len(perps)} mercados futuros...")
        
        ranked_assets = []
        
        for t in perps:
            symbol = t['symbol']
            volume = float(t.get('quoteVolume', 0))
            price = float(t['lastPrice'])
            funding = float(t.get('fundingRate', 0))
            
            # Spread Analysis (Liquidez)
            best_ask = float(t.get('bestAsk', 0) or t.get('ask', 0))
            best_bid = float(t.get('bestBid', 0) or t.get('bid', 0))
            
            spread = 0
            if best_bid > 0:
                spread = (best_ask - best_bid) / best_bid
            
            # Smart Money Score
            # 1. Volume: Quanto maior, mais interesse.
            # 2. Funding: 
            #    - Positivo Alto (>0.01%): Bullish Aggressive (Longs pagando)
            #    - Negativo Alto (<-0.01%): Bearish Aggressive (Shorts pagando)
            #    - Neutro (0.00% - 0.005%): Acumulação/Distribuição
            
            # Categorização
            flow_type = "NEUTRAL"
            if funding > 0.015: flow_type = "BULLISH_FOMO"
            elif funding > 0.005: flow_type = "BULLISH_STEADY"
            elif funding < -0.015: flow_type = "BEARISH_DUMP"
            elif funding < -0.005: flow_type = "BEARISH_HEDGE"
            
            # Whales preferem liquidez (Spread baixo)
            liquidity_score = 0
            if spread < 0.0005: liquidity_score = 10 # Spread < 0.05% (Elite)
            elif spread < 0.0010: liquidity_score = 7  # Spread < 0.10% (Good)
            else: liquidity_score = 2
            
            ranked_assets.append({
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "funding": funding,
                "spread": spread,
                "flow": flow_type,
                "liquidity_score": liquidity_score
            })
            
        # Ordenar por Volume (Onde está o dinheiro)
        ranked_assets.sort(key=lambda x: x['volume'], reverse=True)
        
        print("\n TOP 10 ATIVOS POR VOLUME (Fluxo de Capital):")
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'VOLUME (24h)':<15} | {'FUNDING':<10} | {'SPREAD':<8} | {'FLOW TYPE'}")
        print("-" * 85)
        
        for asset in ranked_assets[:10]:
            vol_fmt = f"${asset['volume']/1000000:.1f}M"
            fund_fmt = f"{asset['funding']*100:.4f}%"
            spread_fmt = f"{asset['spread']*100:.2f}%"
            
            print(f"{asset['symbol']:<15} | ${asset['price']:<9.2f} | {vol_fmt:<15} | {fund_fmt:<10} | {spread_fmt:<8} | {asset['flow']}")

        # Análise de Oportunidades "Hidden Gem" (Volume Decente + Funding Neutro + Spread Baixo)
        # Onde as baleias acumulam sem chamar atenção.
        print("\n HIDDEN GEMS (Acumulação Silenciosa?):")
        print("Critério: Volume > $1M, Funding Baixo, Spread < 0.05%")
        
        hidden_gems = [
            a for a in ranked_assets 
            if a['volume'] > 1000000 
            and abs(a['funding']) < 0.005 
            and a['spread'] < 0.0008
        ]
        
        if hidden_gems:
             for asset in hidden_gems[:5]:
                vol_fmt = f"${asset['volume']/1000000:.1f}M"
                print(f" {asset['symbol']} ({vol_fmt}) - Funding Flat ({asset['funding']*100:.4f}%)")
        else:
            print("   Nenhuma Hidden Gem clara detectada.")

        # Análise de Funding Extremo (Onde a batalha está ocorrendo)
        print("\n ZONA DE GUERRA (Funding Extremo):")
        war_zones = [a for a in ranked_assets if abs(a['funding']) > 0.015]
        if war_zones:
            for asset in war_zones[:5]:
                direction = "LONG SQUEEZE" if asset['funding'] < 0 else "SHORT SQUEEZE"
                print(f"️ {asset['symbol']} - Funding: {asset['funding']*100:.4f}% ({direction})")
        else:
            print("   Funding rates normais. Sem stress sistêmico.")

if __name__ == "__main__":
    scanner = SmartMoneyScanner()
    scanner.scan()
