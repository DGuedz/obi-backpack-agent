import os
import sys
import pandas as pd
import numpy as np
import time
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport

init(autoreset=True)
load_dotenv()

class MarketBrief:
    def __init__(self):
        self.transport = BackpackTransport()
        self.symbols = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"]
        self.timeframes = ["1d", "6h", "4h", "2h", "1h", "30m", "15m", "5m", "3m", "1m"]

    def calculate_indicators(self, klines):
        if not klines or len(klines) < 50:
            return None
        
        df = pd.DataFrame(klines)
        # Backpack Klines: [open, high, low, close, volume] (verificar ordem exata se dict ou list)
        # O transport retorna lista de dicts geralmente, mas vamos checar.
        # No transport.py: return resp.json() -> é uma lista de dicts: {'open':..., 'close':...}
        
        # Converter para numeric
        df['close'] = pd.to_numeric(df['close'])
        
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMAs
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        return df.iloc[-1]

    def get_trend_color(self, row):
        price = row['close']
        ema20 = row['ema20']
        ema50 = row['ema50']
        
        if price > ema20 and ema20 > ema50:
            return Fore.GREEN + "BULLISH"
        elif price < ema20 and ema20 < ema50:
            return Fore.RED + "BEARISH"
        else:
            return Fore.YELLOW + "NEUTRAL"

    def get_rsi_color(self, rsi):
        if rsi > 70: return Fore.RED + f"{rsi:.1f} (OB)"
        if rsi < 30: return Fore.GREEN + f"{rsi:.1f} (OS)"
        return Fore.WHITE + f"{rsi:.1f}"

    def run(self):
        print(f"\n{Style.BRIGHT} OBIWORK MARKET BRIEFING - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for symbol in self.symbols:
            print(f"\n{Fore.CYAN} {symbol}{Style.RESET_ALL}")
            print(f"{'TF':<6} | {'PRICE':<10} | {'TREND':<10} | {'RSI':<10} | {'EMA20':<10} | {'EMA50':<10}")
            print("-" * 65)
            
            score = 0
            
            for tf in self.timeframes:
                klines = self.transport.get_klines(symbol, tf, limit=100)
                data = self.calculate_indicators(klines)
                
                if data is None:
                    print(f"{tf:<6} | {'WAITING DATA...':<40}")
                    continue
                
                trend_str = self.get_trend_color(data)
                rsi_str = self.get_rsi_color(data['rsi'])
                
                # Scoring Simples
                if "BULLISH" in trend_str: score += 1
                if "BEARISH" in trend_str: score -= 1
                
                print(f"{tf:<6} | {data['close']:<10.2f} | {trend_str:<19} | {rsi_str:<19} | {data['ema20']:<10.2f} | {data['ema50']:<10.2f}")
            
            print("-" * 65)
            veredicto = "NEUTRO"
            color = Fore.YELLOW
            if score >= 3: 
                veredicto = "COMPRA FORTE"
                color = Fore.GREEN
            elif score <= -3: 
                veredicto = "VENDA FORTE"
                color = Fore.RED
                
            print(f"{Style.BRIGHT}VEREDICTO FINAL: {color}{veredicto} (Score: {score}){Style.RESET_ALL}")

if __name__ == "__main__":
    brief = MarketBrief()
    brief.run()
