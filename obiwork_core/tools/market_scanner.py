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
from technical_oracle import TechnicalOracle

init(autoreset=True)
load_dotenv()

class MarketScanner:
    def __init__(self):
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data)

    async def scan(self):
        print(f"\n{Style.BRIGHT} OBIWORK SATELLITE SCANNER - {time.strftime('%H:%M:%S')}")
        print("=" * 100)
        print(f" Varrendo Backpack em busca de Volume e Fluxo (OBI)...")

        # 1. Get All Tickers
        tickers = self.transport._send_request("GET", "/api/v1/tickers", "tickerQueryAll")
        if not tickers:
            print(" Erro ao buscar tickers.")
            return

        # 2. BTC Reference (Compass)
        btc_ticker = next((t for t in tickers if t['symbol'] == 'BTC_USDC_PERP'), None)
        btc_trend = "NEUTRAL"
        btc_obi = 0.0
        
        if btc_ticker:
            btc_change = float(btc_ticker['priceChangePercent'])
            btc_depth = self.data.get_orderbook_depth('BTC_USDC_PERP')
            if btc_depth:
                btc_obi = self.oracle.calculate_obi(btc_depth)
            
            trend_color = Fore.GREEN if btc_change > 0 else Fore.RED
            obi_color = Fore.GREEN if btc_obi > 0.1 else (Fore.RED if btc_obi < -0.1 else Fore.YELLOW)
            
            print(f"\n {Style.BRIGHT}BTC REFERENCE:{Style.RESET_ALL} Price {btc_ticker['lastPrice']} ({trend_color}{btc_change:.2f}%{Style.RESET_ALL}) | OBI: {obi_color}{btc_obi:.2f}{Style.RESET_ALL}")
            
            if btc_obi > 0.15: btc_trend = "BULLISH"
            elif btc_obi < -0.15: btc_trend = "BEARISH"
            else: btc_trend = "CHOPPY"
            
            print(f"   -> Market Regime: {btc_trend}")

        # 3. Filter Perps & Sort by Volume
        perps = [t for t in tickers if t['symbol'].endswith('_PERP')]
        # Sort by quoteVolume (USDC Volume) descending
        perps.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
        
        top_assets = perps[:15] # Analisar top 15 liquidez

        print(f"\n{Fore.YELLOW}{'SYMBOL':<15} | {'PRICE':<10} | {'24H %':<8} | {'VOL (M)':<8} | {'OBI (FLOW)':<15} | {'VERDICT':<15}")
        print("-" * 105)

        candidates = []

        for asset in top_assets:
            symbol = asset['symbol']
            if symbol == 'BTC_USDC_PERP': continue # Skip BTC (Already analyzed)
            
            price = float(asset['lastPrice'])
            change_24h = float(asset['priceChangePercent'])
            volume_m = float(asset['quoteVolume']) / 1_000_000
            
            # Deep Dive (OBI Analysis)
            depth = self.data.get_orderbook_depth(symbol)
            if not depth:
                continue
                
            obi = self.oracle.calculate_obi(depth)
            
            # Color Coding
            obi_color = Fore.GREEN if obi > 0.2 else (Fore.RED if obi < -0.2 else Fore.WHITE)
            change_color = Fore.GREEN if change_24h > 0 else Fore.RED
            
            # Verdict Logic
            verdict = "WAIT"
            verdict_color = Fore.WHITE
            
            # Correlation Logic
            # Se BTC é BULLISH, procuramos ALTS com OBI > 0.2
            # Se BTC é BEARISH, procuramos ALTS com OBI < -0.2
            
            is_correlated = False
            if btc_trend == "BULLISH" and obi > 0.2: is_correlated = True
            if btc_trend == "BEARISH" and obi < -0.2: is_correlated = True
            
            # Confluência: Preço subindo + OBI Positivo (Compra Real)
            if change_24h > 0 and obi > 0.2:
                verdict = "STRONG LONG"
                verdict_color = Fore.GREEN
                score = obi + (change_24h/100)
                if is_correlated: score *= 1.5 # Boost se alinhado com BTC
                candidates.append({'symbol': symbol, 'score': score, 'side': 'LONG'})
            
            # Confluência: Preço caindo + OBI Negativo (Venda Real)
            elif change_24h < 0 and obi < -0.2:
                verdict = "STRONG SHORT"
                verdict_color = Fore.RED
                score = abs(obi) + abs(change_24h/100)
                if is_correlated: score *= 1.5
                candidates.append({'symbol': symbol, 'score': score, 'side': 'SHORT'})
                
            # Divergência (Trap) ou Oportunidade de Reversão
            # Ex: BTC subindo, ALT caindo mas com OBI Positivo (Lagging Pump?)
            elif btc_trend == "BULLISH" and change_24h < 0 and obi > 0.25:
                 verdict = "LAGGING PUMP?"
                 verdict_color = Fore.CYAN
                 candidates.append({'symbol': symbol, 'score': obi * 2, 'side': 'LONG (Reversal)'})

            print(f"{symbol:<15} | {price:<10.4f} | {change_color}{change_24h:>7.2f}%{Style.RESET_ALL} | {volume_m:>7.1f}M | {obi_color}{obi:>14.2f}{Style.RESET_ALL} | {verdict_color}{verdict:<15}")

        print("-" * 105)
        
        # Recommendation
        if candidates:
            candidates.sort(key=lambda x: x['score'], reverse=True)
            best_3 = candidates[:3]
            print(f"\n{Style.BRIGHT} TOP 3 ALVOS EM CONFLUÊNCIA COM BTC ({btc_trend}):")
            for c in best_3:
                side_color = Fore.GREEN if 'LONG' in c['side'] else Fore.RED
                print(f"    {c['symbol']} -> {side_color}{c['side']}{Style.RESET_ALL} (Score: {c['score']:.2f})")
        else:
            print("\n️ Nenhum ativo com confluência forte encontrado no momento.")

if __name__ == "__main__":
    scanner = MarketScanner()
    asyncio.run(scanner.scan())
