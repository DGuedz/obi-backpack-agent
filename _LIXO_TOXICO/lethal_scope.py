import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from market_intelligence import MarketIntelligence

load_dotenv()

class LethalScope:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.mi = MarketIntelligence()
        
    def activate_scope(self):
        print(" LETHAL SCOPE: MIRA ATIVADA (One Shot, One Kill)")
        print("================================================")
        print("   Critérios de Disparo (Confluência Tripla):")
        print("   1. RSI Extremo (< 30 ou > 70)")
        print("   2. Bollinger Break (Preço fora das bandas)")
        print("   3. Volume Spike (> 1.5x Média)")
        print("------------------------------------------------")
        
        # 1. Get Top Liquid Assets
        tickers = self.data.get_tickers()
        liquid_perps = [t for t in tickers if 'PERP' in t['symbol'] and float(t.get('quoteVolume', 0)) > 5_000_000]
        
        targets_found = 0
        
        print(f" Monitorando {len(liquid_perps)} alvos prioritários...", flush=True)
        
        for t in liquid_perps:
            symbol = t['symbol']
            price = float(t['lastPrice'])
            volume_24h = float(t.get('quoteVolume', 0))
            
            # Fetch Klines (15m for Sniper)
            klines = self.data.get_klines(symbol, "15m", limit=30)
            if not klines or len(klines) < 25: continue
            
            closes = [float(k['close']) for k in klines]
            volumes = [float(k['volume']) for k in klines]
            
            # 1. RSI Check
            rsi = self.mi.calculate_rsi(closes)
            
            # 2. Bollinger Check
            bb_upper, bb_mid, bb_lower = self.mi.calculate_bollinger_bands(closes)
            
            # 3. Volume Check (Last candle vs Avg 20)
            last_vol = volumes[-1]
            avg_vol = sum(volumes[-21:-1]) / 20 if len(volumes) > 20 else last_vol
            vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1.0
            
            # --- THE LETHAL FILTER ---
            signal = None
            
            # LONG SETUP
            if rsi < 30 and price <= bb_lower * 1.001: # Touching lower band
                if vol_ratio > 1.5:
                    signal = "🟢 SNIPER LONG"
            
            # SHORT SETUP
            elif rsi > 70 and price >= bb_upper * 0.999: # Touching upper band
                if vol_ratio > 1.5:
                    signal = " SNIPER SHORT"
            
            if signal:
                print(f"\n ALVO NA MIRA: {symbol}")
                print(f"   Sinal: {signal}")
                print(f"   Preço: ${price} (BB: {bb_lower:.4f} - {bb_upper:.4f})")
                print(f"   RSI: {rsi:.1f} | Vol Ratio: {vol_ratio:.1f}x")
                print(f"   >>> PRONTO PARA DISPARO MANUAL <<<")
                targets_found += 1
            # else:
            #     # Optional: Show 'Near Misses' for confidence
            #     if rsi < 35 or rsi > 65:
            #         print(f"   ️ {symbol} próximo... (RSI {rsi:.1f})")

        if targets_found == 0:
            print("\n Vento calmo. Nenhum alvo no centro da mira.")
            print("   Status: AGUARDANDO (Disciplina de Sniper).")
        else:
            print(f"\n {targets_found} Oportunidades Letais Detectadas!")

if __name__ == "__main__":
    scope = LethalScope()
    scope.activate_scope()
