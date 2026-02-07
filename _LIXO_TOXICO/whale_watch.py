#!/usr/bin/env python3
"""
 Whale Watch - Anomaly Detector & Trap Setter
Monitora picos de volume anormais para antecipar movimentos de baleias.
"""

import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class WhaleWatch:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.symbols = ['SOL_USDC_PERP', 'ETH_USDC_PERP', 'BTC_USDC_PERP', 'PYTH_USDC_PERP']
        self.history = {s: [] for s in self.symbols}

    def scan(self):
        print("\n Whale Watch: Sonar Ativado...")
        print("   Monitorando anomalias de volume (3x Média)...")
        print("=================================================")
        
        while True:
            try:
                for symbol in self.symbols:
                    ticker = self.data.get_ticker(symbol)
                    if not ticker: continue
                    
                    price = float(ticker['lastPrice'])
                    # Volume Quote é o volume em USD das últimas 24h.
                    # Para detectar picos instantâneos, precisaríamos de klines de 1m.
                    
                    klines = self.data.get_klines(symbol, "1m", limit=5)
                    if not klines: continue
                    
                    # Analisar o candle atual (fechado ou em aberto)
                    last_candle = klines[-1]
                    volume_now = float(last_candle.get('volume', 0)) # Volume do candle atual
                    
                    # Média dos últimos 5 candles
                    volumes = [float(k.get('volume', 0)) for k in klines[:-1]]
                    if not volumes: continue
                    
                    avg_vol = sum(volumes) / len(volumes)
                    
                    # Fator de Anomalia
                    if avg_vol > 0:
                        factor = volume_now / avg_vol
                    else:
                        factor = 0
                        
                    # Detecção
                    if factor > 3.0: # 3x o volume médio recente
                        print(f" BALEIA DETECTADA EM {symbol}!")
                        print(f"    Volume: {factor:.1f}x a média")
                        print(f"    Preço: ${price}")
                        
                        # Análise de Direção (Price Action do Candle)
                        open_p = float(last_candle['open'])
                        close_p = float(last_candle['close'])
                        
                        if close_p > open_p:
                            print("   🟢 AÇÃO: COMPRA MASSIVA (Pump Imminent?)")
                            print("    GATILHO SUGERIDO: Phoenix Long Breakout")
                        else:
                            print("    AÇÃO: DESPEJO (Dump Incoming?)")
                            print("    GATILHO SUGERIDO: Weaver Short Bias")
                            
                        print("-" * 40)
                    
                time.sleep(10) # Scan a cada 10s
                
            except Exception as e:
                print(f" Erro no sonar: {e}")
                time.sleep(10)

if __name__ == "__main__":
    watcher = WhaleWatch()
    watcher.scan()