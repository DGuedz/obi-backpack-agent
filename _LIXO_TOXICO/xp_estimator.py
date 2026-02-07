#!/usr/bin/env python3
"""
 XP Estimator - Backpack Season Tracker
Calcula o volume total gerado para estimar o ranking na Season.
"""

import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class XPEstimator:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def calculate(self):
        print("\n Calculating Total Trading Volume (XP Proxy)...")
        print("================================================")
        
        try:
            # Buscar histórico (limite máximo permitido pela API, geralmente 1000)
            # Para histórico completo, precisaríamos paginar com 'offset' ou 'lastId'.
            # Vamos tentar pegar os últimos 1000 trades para ter uma ideia recente.
            fills = self.data.get_fill_history(limit=1000)
            
            if not fills:
                print(" Nenhum histórico de trades encontrado (ou erro na API).")
                return

            total_volume = 0.0
            maker_volume = 0.0
            taker_volume = 0.0
            trades_count = len(fills)
            
            for trade in fills:
                # Estrutura do fill: {'price': '...', 'quantity': '...', 'isMaker': True/False, ...}
                price = float(trade.get('price', 0))
                qty = float(trade.get('quantity', 0))
                notional = price * qty
                
                total_volume += notional
                
                if trade.get('isMaker', False):
                    maker_volume += notional
                else:
                    taker_volume += notional
            
            print(f" Trades Analisados: {trades_count}")
            print(f" Volume Total: ${total_volume:,.2f}")
            print("-" * 40)
            print(f" Maker Volume: ${maker_volume:,.2f} ({(maker_volume/total_volume)*100:.1f}%)")
            print(f" Taker Volume: ${taker_volume:,.2f} ({(taker_volume/total_volume)*100:.1f}%)")
            print("-" * 40)
            
            # Estimativa de XP (Chute base: 10 pts por $1 Maker, 1 pt por $1 Taker - Varia muito!)
            # Isso é apenas ilustrativo para gamificação.
            est_xp = (maker_volume * 10) + (taker_volume * 1)
            print(f" XP Estimado (Score): {int(est_xp):,}")
            
            if total_volume > 100000:
                print(" Rank Estimado: WHALE ")
            elif total_volume > 10000:
                print(" Rank Estimado: SHARK ")
            elif total_volume > 1000:
                print(" Rank Estimado: DOLPHIN ")
            else:
                print(" Rank Estimado: SHRIMP ")

        except Exception as e:
            print(f" Erro ao calcular XP: {e}")

if __name__ == "__main__":
    estimator = XPEstimator()
    estimator.calculate()