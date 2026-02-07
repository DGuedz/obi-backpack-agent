import os
import sys
import pandas as pd
import asyncio
import time
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

init(autoreset=True)
load_dotenv()

class SwingScanner:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)

    def calculate_indicators(self, df):
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid division by zero
        rs = gain / loss
        rs = rs.fillna(0)
        
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA 50
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        return df

    async def scan(self):
        print(f"\n{Style.BRIGHT} OBIWORK SWING SCANNER (4H) - {time.strftime('%H:%M:%S')}")
        print("=" * 100)
        print(f"{'SYMBOL':<15} | {'PRICE':<12} | {'RSI (4H)':<10} | {'TREND (EMA50)':<15} | {'VERDICT':<15}")
        print("-" * 100)
        
        tickers = self.data.get_tickers()
        if not tickers:
            print(" Error fetching tickers")
            return

        # Filter and sort by volume
        perps = [t for t in tickers if 'PERP' in t['symbol']]
        top_perps = sorted(perps, key=lambda x: float(x['quoteVolume']), reverse=True)[:12]

        for t in top_perps:
            symbol = t['symbol']
            price = float(t['lastPrice'])
            
            # Fetch 4h Klines
            klines = self.data.get_klines(symbol, '4h', limit=100)
            if not klines or len(klines) < 50:
                continue
                
            try:
                # Backpack API returns list of dicts with 'close' as string
                df = pd.DataFrame(klines)
                if 'close' not in df.columns:
                    continue
                    
                df['close'] = df['close'].astype(float)
                
                df = self.calculate_indicators(df)
                last_row = df.iloc[-1]
                
                rsi = last_row['rsi']
                ema50 = last_row['ema50']
                
                trend = "BULLISH" if price > ema50 else "BEARISH"
                trend_color = Fore.GREEN if trend == "BULLISH" else Fore.RED
                
                rsi_color = Fore.YELLOW
                if rsi > 70: rsi_color = Fore.RED # Overbought
                if rsi < 30: rsi_color = Fore.GREEN # Oversold
                
                verdict = "WAIT"
                verdict_color = Fore.WHITE
                
                # Logic: Trend Following Pullback or Reversal
                if trend == "BULLISH" and rsi < 45: 
                    verdict = "LONG (DIP)"
                    verdict_color = Fore.GREEN
                elif trend == "BEARISH" and rsi > 55:
                    verdict = "SHORT (RALLY)"
                    verdict_color = Fore.RED
                elif trend == "BULLISH" and rsi > 70:
                    verdict = "TAKE PROFIT"
                    verdict_color = Fore.YELLOW
                elif trend == "BEARISH" and rsi < 30:
                    verdict = "COVER SHORT"
                    verdict_color = Fore.GREEN
                
                print(f"{symbol:<15} | {price:<12.4f} | {rsi_color}{rsi:<10.2f}{Style.RESET_ALL} | {trend_color}{trend:<15}{Style.RESET_ALL} | {verdict_color}{verdict:<15}{Style.RESET_ALL}")
                
            except Exception as e:
                # print(f"Error parsing {symbol}: {e}")
                pass

if __name__ == "__main__":
    scanner = SwingScanner()
    asyncio.run(scanner.scan())
