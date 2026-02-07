import pandas as pd
import numpy as np
from datetime import datetime

class AirdropAnalyzer:
    def __init__(self):
        # Dados fornecidos pelo usuário
        self.total_volume = 1_968_170.60  # $1.96M
        
        # Estrutura de Pontos por Season
        self.seasons = {
            'S1': {
                'points': 597,
                'rank': 'Silver',
                'weeks': {
                    'Bonus': 3, 'W10': 3, 'W9': 3, 'W8': 103, 'W7': 284, 
                    'W6': 98, 'W5': 103, 'W4': 0, 'W3': 0, 'W2': 0, 'W1': 0
                }
            },
            'S3': {
                'points': 229, # Total oficial do print
                'rank': 'Silver',
                'weeks': {
                    # Nota: W1 mostra 508 no texto mas total é 229. 
                    # Assumindo ajuste/decay ou erro de OCR no texto do usuário.
                    # Usaremos os dados brutos para tendência, mas total oficial para cálculo.
                    'W1': 508, 'W2': 103, 'W3': 80, 'W4': 101, 'W5': 102, 
                    'W6': 29, 'W7': 3, 'W8': 0, 'W9': 0, 'W10': 0
                }
            },
            'S4': {
                'points': 1247,
                'rank': 'Gold',
                'weeks': {
                    'W9': 837, 'W8': 406, 'W3': 3, 'W2': 1, 
                    'Others': 0
                }
            }
        }
        
        # Volume Breakdown (Estimado dos Levels dos prints)
        self.assets = {
            'SOL-PERP': {'level': 14, 'min_vol': 320_000, 'max_vol': 640_000},
            'BTC-PERP': {'level': 14, 'min_vol': 320_000, 'max_vol': 640_000},
            'ETH-PERP': {'level': 13, 'min_vol': 160_000, 'max_vol': 320_000},
            'LIT-PERP': {'level': 13, 'min_vol': 160_000, 'max_vol': 320_000},
            'HYPE-PERP': {'level': 12, 'min_vol': 80_000, 'max_vol': 160_000},
            'IP-PERP': {'level': 11, 'min_vol': 40_000, 'max_vol': 80_000},
            'SKR-PERP': {'level': 11, 'min_vol': 40_000, 'max_vol': 80_000},
            'BNB-PERP': {'level': 11, 'min_vol': 40_000, 'max_vol': 80_000},
            # Outros menores agregados para bater o total
        }

    def analyze_costs(self):
        """Calcula custos estimados baseados em taxas de taker/maker"""
        # Backpack Fees (Estimativa média para usuários normais/vip baixo)
        # Taker: 0.08% (padrão) -> 0.05% (com desconto/volume)
        # Maker: 0.02% -> 0.00%
        
        scenarios = {
            'Aggressive Taker (0.07%)': 0.0007,
            'Balanced (0.04%)': 0.0004,
            'Efficient Maker (0.02%)': 0.0002
        }
        
        total_points = sum(s['points'] for s in self.seasons.values())
        
        print("\n ANÁLISE DE CUSTOS E EFICIÊNCIA")
        print("="*60)
        print(f"Volume Total: ${self.total_volume:,.2f}")
        print(f"Total Pontos: {total_points}")
        print(f"Eficiência de Volume: ${self.total_volume / total_points:.2f} volume por ponto")
        
        print("\n Estimativa de Custos (Taxas Pagas):")
        for name, fee in scenarios.items():
            cost = self.total_volume * fee
            cpa = cost / total_points if total_points > 0 else 0
            print(f"  • {name:<25}: ${cost:,.2f} total | ${cpa:.2f} por ponto")
            
        return total_points

    def analyze_seasons(self):
        """Analisa performance por season"""
        print("\n ANÁLISE POR TEMPORADA")
        print("="*60)
        
        for name, data in self.seasons.items():
            print(f"\n{name} ({data['rank']}): {data['points']} Pontos")
            
            # Identificar melhores semanas
            sorted_weeks = sorted(data['weeks'].items(), key=lambda x: x[1], reverse=True)
            top_3 = sorted_weeks[:3]
            
            print(f"   Top Semanas:")
            for w, p in top_3:
                if p > 0:
                    print(f"     - {w}: {p} pts")
            
            # Análise qualitativa
            if name == 'S4':
                print(f"   Destaque: Aceleração massiva na reta final (W8-W9).")
                print(f"     Representa {data['points']/2073*100:.1f}% de todos os seus pontos.")

    def project_airdrop_value(self, total_points):
        """Projeta valor do airdrop baseado em comps de mercado"""
        # Comparáveis: Jupiter, Jito, Pyth (Valor por ponto varia muito)
        # Estimativa conservadora: $0.20 - $0.50 por ponto
        # Estimativa otimista: $1.00 - $2.00 por ponto (se market cap for alto)
        
        scenarios = [0.10, 0.30, 0.50, 1.00, 2.00]
        
        print("\n PROJEÇÃO DE VALOR DO AIRDROP")
        print("="*60)
        print(f"Base de Cálculo: {total_points} Pontos Totais")
        print("\nCenário | Preço/Ponto | Valor Total Estimado | ROI (Base Custo $0.04%)")
        print("-" * 75)
        
        est_cost = self.total_volume * 0.0004 # $787
        
        for price in scenarios:
            value = total_points * price
            roi = ((value - est_cost) / est_cost) * 100
            print(f"  {'$'+str(price):<6}| ${value:,.2f}      | {roi:>.0f}%")

    def run(self):
        print(" RELATÓRIO DE PERFORMANCE BACKPACK - DOUBLEGREEN")
        total_points = self.analyze_costs()
        self.analyze_seasons()
        self.project_airdrop_value(total_points)

if __name__ == "__main__":
    analyzer = AirdropAnalyzer()
    analyzer.run()
