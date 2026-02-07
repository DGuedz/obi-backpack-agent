import sys
import os
import time
import pandas as pd
import numpy as np
import requests

# Adicionar diretório atual ao path para imports
sys.path.append(os.getcwd())

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from feedback_department import FeedbackDepartment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configurações ---
TIMEFRAME = "1h"  # Analisar no 1H para consistência
LIMIT_CANDLES = 100
RSI_PERIOD = 14
BB_PERIOD = 20
BB_STD = 2.0

class OpportunityScanner:
    def __init__(self):
        api_key = os.getenv('BACKPACK_API_KEY')
        private_key = os.getenv('BACKPACK_API_SECRET')
        if not api_key or not private_key:
            raise ValueError("API Credentials not found in .env")
            
        self.auth = BackpackAuth(api_key, private_key)
        self.data = BackpackData(self.auth)
        self.feedback = FeedbackDepartment()

    def calculate_indicators(self, klines):
        if not klines or len(klines) < BB_PERIOD:
            return None
        
        # Klines format: { "start": "...", "open": "...", "high": "...", "low": "...", "close": "...", "volume": "...", "trades": "..." }
        # Or list of dicts. Let's assume list of dicts based on standard Backpack API
        
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['sma'] = df['close'].rolling(window=BB_PERIOD).mean()
        df['std'] = df['close'].rolling(window=BB_PERIOD).std()
        df['bb_upper'] = df['sma'] + (BB_STD * df['std'])
        df['bb_lower'] = df['sma'] - (BB_STD * df['std'])
        
        # Volume Spike (vs Avg 20)
        df['vol_avg'] = df['volume'].rolling(window=20).mean()
        
        return df.iloc[-1]

    def scan_market(self):
        print(f" Iniciando Varredura de Mercado ({TIMEFRAME})...")
        markets = self.data.get_markets()
        perp_markets = [m for m in markets if 'PERP' in m['symbol']]
        print(f" Analisando {len(perp_markets)} pares PERP na Backpack...")
        
        opportunities = []
        
        for market in perp_markets:
            symbol = market['symbol']
            # print(f"   Analyzing {symbol}...", end='\r')
            
            try:
                klines = self.data.get_klines(symbol, interval=TIMEFRAME, limit=LIMIT_CANDLES)
                if not klines:
                    continue
                    
                last_candle = self.calculate_indicators(klines)
                
                if last_candle is None or pd.isna(last_candle['rsi']):
                    continue
                
                rsi = last_candle['rsi']
                price = last_candle['close']
                bb_upper = last_candle['bb_upper']
                bb_lower = last_candle['bb_lower']
                volume = last_candle['volume']
                vol_avg = last_candle['vol_avg']
                
                # --- Lógica do Setup 10x ---
                setup_type = None
                confidence = "Medium"
                
                # 1. Oversold Extreme (Long)
                if rsi < 30:
                    setup_type = "OVERSOLD (LONG)"
                    if price <= bb_lower:
                        confidence = "HIGH (Confluence BB)"
                
                # 2. Overbought Extreme (Short)
                elif rsi > 70:
                    setup_type = "OVERBOUGHT (SHORT)"
                    if price >= bb_upper:
                        confidence = "HIGH (Confluence BB)"
                
                # 3. Volume Spike (Momentum)
                elif volume > 2.5 * vol_avg:
                    if rsi > 50:
                        setup_type = "VOL SPIKE (BULL)"
                    else:
                        setup_type = "VOL SPIKE (BEAR)"
                
                if setup_type:
                    opportunities.append({
                        "symbol": symbol,
                        "price": price,
                        "rsi": round(rsi, 2),
                        "setup": setup_type,
                        "confidence": confidence,
                        "vol_mult": round(volume/vol_avg, 1) if vol_avg > 0 else 0
                    })
                    
            except Exception as e:
                # print(f"Error {symbol}: {e}")
                continue
                
        # Ordenar por Confiança e RSI Extremo
        opportunities.sort(key=lambda x: (x['confidence'] == 'HIGH', abs(x['rsi'] - 50)), reverse=True)
        
        print("\n --- RESULTADOS DA ANÁLISE (SETUP 10X) ---")
        if not opportunities:
            print("Nenhuma oportunidade clara encontrada com os parâmetros atuais.")
        else:
            print(f"{'SYMBOL':<15} {'PRICE':<10} {'RSI':<6} {'SETUP':<20} {'CONFIDENCE':<20} {'VOL x'}")
            print("-" * 80)
            for op in opportunities:
                print(f"{op['symbol']:<15} {op['price']:<10.4f} {op['rsi']:<6} {op['setup']:<20} {op['confidence']:<20} {op['vol_mult']}")
        
        print("\n RECOMENDAÇÃO:")
        print("Para o Setup 10x ($100, 2% SL, 5% TP):")
        print("- Escolha pares com 'HIGH' confidence.")
        print("- Verifique o Order Book antes de entrar (Liquidez).")
        print("- Use Limit Orders (Maker) para reduzir taxas.")

if __name__ == "__main__":
    scanner = OpportunityScanner()
    scanner.scan_market()
