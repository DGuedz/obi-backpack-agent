import os
import sys
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.getcwd())

from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# Load environment variables
load_dotenv()

# Configuration
RSI_PERIOD = 14
VOLUME_THRESHOLD = 1_000_000 # Minimum $1M volume
FUNDING_WEIGHT = 40
RSI_WEIGHT = 30
VOLUME_WEIGHT = 30

class GoldenEquationCalculator:
    def __init__(self):
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.private_key = os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(self.api_key, self.private_key)
        self.data = BackpackData(self.auth)
        
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50.0 # Neutral default
            
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
            
        return rsi[-1]

    def get_market_data(self):
        print(" Fetching Market Data...")
        
        # 1. Get Mark Prices (Funding Rates)
        mark_prices = self.data.get_mark_prices()
        if not mark_prices:
            print(" Failed to fetch mark prices.")
            return []
            
        # Create map: symbol -> funding_rate
        funding_map = {}
        if isinstance(mark_prices, list):
            for m in mark_prices:
                funding_map[m['symbol']] = float(m.get('fundingRate', 0))
        elif isinstance(mark_prices, dict):
             # Handle possible dict response
             pass
             
        # 2. Get Tickers (Volume)
        tickers = self.data.get_tickers()
        if not tickers:
            print(" Failed to fetch tickers.")
            return []
            
        # Map tickers by symbol for easy access
        ticker_map = {t['symbol']: t for t in tickers}
        
        perp_markets = [m for m in ticker_map.keys() if 'PERP' in m]
        results = []
        
        print(f" Analyzing {len(perp_markets)} PERP pairs...")
        
        for symbol in perp_markets:
            ticker = ticker_map.get(symbol)
            if not ticker:
                continue
                
            # Basic Data
            price = float(ticker['lastPrice'])
            volume = float(ticker['quoteVolume'])
            
            # Funding from Mark Prices
            funding = funding_map.get(symbol, 0.0) * 100 # Percentage
            
            # Filter by Volume
            if volume < VOLUME_THRESHOLD:
                continue
                
            # Get Candles for RSI (1h timeframe for trend/swing)
            klines = self.data.get_klines(symbol, "1h", limit=30)
            if not klines:
                continue
                
            closes = [float(k['close']) for k in klines]
            rsi = self.calculate_rsi(closes, RSI_PERIOD)
            
            # --- THE GOLDEN EQUATION ---
            # Score logic: High RSI + High Positive Funding = High Short Score
            # Score logic: Low RSI + High Negative Funding = High Long Score
            
            # Normalize inputs
            # Funding: 0.01% is baseline. 0.05% is high. Cap at 0.1%.
            norm_funding = min(abs(funding) / 0.05, 2.0) 
            
            # RSI Deviation from 50
            # RSI 70 -> diff 20. RSI 30 -> diff 20. Max diff 50.
            rsi_dev = abs(rsi - 50)
            norm_rsi = min(rsi_dev / 20.0, 2.0)
            
            # Volume: Log scale to dampen huge differences
            # $1M -> 0, $10M -> 1, $100M -> 2
            norm_vol = min(np.log10(volume / VOLUME_THRESHOLD), 3.0)
            
            # Calculate Raw Score
            raw_score = (norm_funding * FUNDING_WEIGHT) + (norm_rsi * RSI_WEIGHT) + (norm_vol * VOLUME_WEIGHT)
            
            # Determine Direction
            direction = "NEUTRAL"
            setup_quality = "LOW"
            
            if rsi > 65 and funding > 0.01:
                direction = "SHORT (Whale Profit Taking)"
                setup_quality = "HIGH" if rsi > 75 else "MEDIUM"
            elif rsi < 35 and funding < -0.005:
                direction = "LONG (Squeeze Reversal)"
                setup_quality = "HIGH" if rsi < 25 else "MEDIUM"
            elif rsi > 70:
                 direction = "SHORT (Overbought)"
            elif rsi < 30:
                 direction = "LONG (Oversold)"
                 
            results.append({
                "symbol": symbol,
                "price": price,
                "volume_m": volume / 1_000_000,
                "funding_pct": funding,
                "rsi": rsi,
                "score": raw_score,
                "direction": direction,
                "setup_quality": setup_quality
            })
            
        return results

    def print_results(self, results):
        # Sort by Score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        print("\n EQUAÇÃO DE OURO ON-CHAIN (Funding x Volume x RSI) ")
        print("=" * 100)
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'VOL ($M)':<8} | {'FUNDING %':<10} | {'RSI(1h)':<7} | {'SCORE':<5} | {'DIRECTION'}")
        print("-" * 100)
        
        top_candidates = []
        
        for r in results[:10]:
            score_display = f"{r['score']:.1f}"
            print(f"{r['symbol']:<15} | ${r['price']:<9.4f} | {r['volume_m']:<8.1f} | {r['funding_pct']:<10.4f} | {r['rsi']:<7.1f} | {score_display:<5} | {r['direction']}")
            
            if "SHORT" in r['direction'] or "LONG" in r['direction']:
                top_candidates.append(r)
                
        print("\n TOP CANDIDATOS PARA REESTRUTURAÇÃO:")
        if not top_candidates:
            print("   Nenhum candidato claro encontrado com os parâmetros atuais.")
        else:
            for c in top_candidates[:3]:
                print(f"    {c['symbol']}: {c['direction']} (Score: {c['score']:.1f})")
                
        # Allocation Plan
        if top_candidates:
            print("\n PLANO DE ALOCAÇÃO DE MARGEM SUGERIDO:")
            count = min(len(top_candidates), 3)
            alloc_per_asset = 100 / count
            print(f"   Dividir margem disponível em {count} partes de {alloc_per_asset:.0f}%")
            print(f"   Alvos: {[c['symbol'] for c in top_candidates[:3]]}")
            print(f"   Estratégia: Mean Reversion (Bollinger Bands + RSI)")

if __name__ == "__main__":
    calc = GoldenEquationCalculator()
    results = calc.get_market_data()
    calc.print_results(results)
