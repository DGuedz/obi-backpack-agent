#!/usr/bin/env python3
"""
 Prediction Scout - Beta Hunter
Monitora a API em busca de novos Mercados de Previsão (Unified Portfolio).
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class PredictionScout:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.known_markets = set()

    def scan(self):
        print("\n Scanning for Prediction Markets (Beta Access)...")
        print("==================================================")
        
        try:
            markets = self.data.get_markets()
            
            new_markets = []
            prediction_markets = []
            
            for m in markets:
                symbol = m['symbol']
                
                # Lógica de Detecção
                # Mercados de previsão geralmente não têm sufixo PERP nem são pares comuns como SOL_USDC
                # Podem ter datas, nomes de eventos ou prefixos especiais.
                # Ex: "TRUMP2026", "BTC-DEC-100K"
                
                is_perp = "PERP" in symbol
                is_spot = "_" in symbol and not is_perp and len(symbol.split('_')[1]) >= 3 # Ex: SOL_USDC
                
                # Se não parece Spot clássico nem Perp clássico, é suspeito (Previsão?)
                if not is_perp and not is_spot:
                    prediction_markets.append(m)
                
                # Também checar metadados se houver (ex: 'type': 'prediction')
                if m.get('type') == 'prediction' or 'PRED' in symbol:
                    prediction_markets.append(m)

            if prediction_markets:
                print(f" ALERTA: {len(prediction_markets)} Mercados de Previsão Detectados!")
                for pm in prediction_markets:
                    print(f"    {pm['symbol']}")
            else:
                print("    Nada novo no front. Apenas Spot e Perps clássicos.")
                
            print(f"    Total Mercados Escaneados: {len(markets)}")
            print(f"    Última Verificação: {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            print(f" Erro no scout: {e}")

if __name__ == "__main__":
    scout = PredictionScout()
    scout.scan()