#!/usr/bin/env python3
"""
️ Omega Scout - High Octane Gem Hunter
Identifica ativos com a combinação perfeita de Volume, Volatilidade e Oportunidade Técnica.
Meta: Encontrar o veículo para atingir $1,000.
"""

import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class OmegaScout:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def analyze_market(self, symbol):
        try:
            # 1. Obter Klines (Velas) para análise técnica
            klines = self.data.get_klines(symbol, "1h", limit=24) # Últimas 24h
            if not klines: return None
            
            df = pd.DataFrame(klines)
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            # 2. Calcular Métricas
            # ATR (Volatilidade)
            df['tr'] = df['high'] - df['low'] # Simplificado
            atr = df['tr'].mean()
            price = df['close'].iloc[-1]
            atr_percent = (atr / price) * 100
            
            # Volume Total 24h (Estimado)
            vol_24h = (df['volume'] * df['close']).sum()
            
            # RSI (Rapidão)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            return {
                'symbol': symbol,
                'price': price,
                'atr_pct': atr_percent,
                'volume': vol_24h,
                'rsi': rsi
            }
            
        except:
            return None

    def scan(self):
        print("\n️ OMEGA SCOUT: Scanning for $1,000 Makers...")
        print("   Criteria: High Volatility + High Liquidity + Technical Setup")
        print("==============================================================")
        
        markets = self.data.get_markets()
        perp_markets = [m['symbol'] for m in markets if "PERP" in m['symbol']]
        
        results = []
        
        print(f"    Analisando {len(perp_markets)} ativos (Deep Scan)...")
        
        for sym in perp_markets:
            # Pular stablecoins e pares mortos conhecidos
            if "USDC_USDC" in sym or "USDT_USDC" in sym: continue
            
            data = self.analyze_market(sym)
            if data:
                results.append(data)
            time.sleep(0.1) # Rate limit friendly
            
        # Filtrar e Ordenar
        # Queremos: Volume > $1M E (RSI < 35 ou RSI > 65)
        # Ordenar por Volatilidade (ATR) -> Mais volatilidade = Mais lucro no Grid/Sniper
        
        # Filtrar lixo sem volume
        candidates = [r for r in results if r['volume'] > 1_000_000]
        
        # Ordenar por ATR (Do mais explosivo para o menos)
        candidates.sort(key=lambda x: x['atr_pct'], reverse=True)
        
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'ATR(1h)':<8} | {'RSI':<5} | {'VOL(24h)'}")
        print("-" * 70)
        
        for c in candidates[:10]:
            # Destacar Oportunidades RSI
            rsi_mark = ""
            if c['rsi'] < 30: rsi_mark = "🟢 BUY"
            elif c['rsi'] > 70: rsi_mark = " SELL"
            
            vol_m = c['volume'] / 1_000_000
            print(f"{c['symbol']:<15} | ${c['price']:<9.4f} | {c['atr_pct']:>6.2f}% | {c['rsi']:>4.1f} {rsi_mark} | ${vol_m:.1f}M")
            
        if candidates:
            best = candidates[0]
            print(f"\n ALVO ESCOLHIDO: {best['symbol']}")
            print(f"    Volatilidade: {best['atr_pct']:.2f}% (Excelente para Weaver)")
            print(f"    Liquidez: ${best['volume']/1_000_000:.1f}M (Seguro para Size)")
            print(f"    Setup: RSI {best['rsi']:.1f}")
        else:
            print("\n️ Nenhuma gema encontrada. Mercado muito parado ou API falhou.")

if __name__ == "__main__":
    scout = OmegaScout()
    scout.scan()