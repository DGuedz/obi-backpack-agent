
import os
import sys
import asyncio
import pandas as pd
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

class HunterReport:
    """
     HUNTER REPORT
    Deep Dive analysis on specific targets to find 'Ambush' zones (Limit Orders).
    """
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data)
        
    def find_liquidity_walls(self, depth, current_price, threshold_ratio=2.0):
        """
        Identifies price levels with significant liquidity (Walls).
        """
        if not depth: return None, None
        
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # Calculate average volume per level to establish a baseline
        avg_bid_vol = sum(float(b[1]) for b in bids[:20]) / 20 if bids else 0
        avg_ask_vol = sum(float(a[1]) for a in asks[:20]) / 20 if asks else 0
        
        support_wall = None
        resistance_wall = None
        
        # Find Support (Bid Wall)
        for price, qty in bids:
            if float(qty) > avg_bid_vol * threshold_ratio:
                support_wall = (float(price), float(qty))
                break # Found the nearest wall
                
        # Find Resistance (Ask Wall)
        for price, qty in asks:
            if float(qty) > avg_ask_vol * threshold_ratio:
                resistance_wall = (float(price), float(qty))
                break # Found the nearest wall
                
        return support_wall, resistance_wall

    async def generate_report(self):
        print(f"\n{Style.BRIGHT} OBIWORK HUNTER REPORT - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 1. Identify Top Movers (Prey)
        tickers = self.data.get_tickers()
        perps = [t for t in tickers if 'symbol' in t and t['symbol'].endswith('_PERP')]
        sorted_movers = sorted(perps, key=lambda x: abs(float(x.get('priceChangePercent', 0))), reverse=True)
        
        targets = ["BTC_USDC_PERP", "SOL_USDC_PERP"] # Always watch the Kings
        
        # Add Top 3 Movers
        count = 0
        for t in sorted_movers:
            if t['symbol'] not in targets:
                targets.append(t['symbol'])
                count += 1
            if count >= 3: break
            
        print(f" ALVOS IDENTIFICADOS: {', '.join(targets)}")
        print("-" * 70)
        
        for symbol in targets:
            # Data Gathering
            ticker = self.data.get_ticker(symbol)
            depth = self.data.get_orderbook_depth(symbol)
            obi = self.oracle.calculate_obi(depth) if depth else 0.0
            price = float(ticker['lastPrice'])
            change_24h = float(ticker['priceChangePercent']) * 100
            
            # Liquidity Walls
            support, resistance = self.find_liquidity_walls(depth, price)
            
            # Trend Analysis (Simple EMA check via Klines)
            klines = self.data.get_klines(symbol, '1h', limit=50)
            df = pd.DataFrame(klines)
            if 'close' in df.columns:
                df['close'] = df['close'].astype(float)
                ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
                trend = "🟢 BULLISH" if price > ema50 else " BEARISH"
            else:
                trend = " NEUTRAL"

            # OBI Sentiment
            obi_color = Fore.GREEN if obi > 0 else Fore.RED
            obi_sentiment = "COMPRADOR" if obi > 0 else "VENDEDOR"
            
            print(f"\n {Style.BRIGHT}{symbol}{Style.RESET_ALL} | {trend} | 24h: {Fore.YELLOW}{change_24h:+.2f}%{Style.RESET_ALL}")
            print(f"    Preço Atual: {price}")
            print(f"    Fluxo OBI: {obi_color}{obi:.2f} ({obi_sentiment}){Style.RESET_ALL}")
            
            if support:
                dist_s = ((price - support[0]) / price) * 100
                print(f"   ️ Parede de Compra (Suporte): {Fore.GREEN}{support[0]}{Style.RESET_ALL} (Vol: {support[1]:.2f}) - Dist: {dist_s:.2f}%")
            else:
                print(f"   ️ Parede de Compra: {Fore.BLACK}Não detectada (Book Fino){Style.RESET_ALL}")
                
            if resistance:
                dist_r = ((resistance[0] - price) / price) * 100
                print(f"    Parede de Venda (Resistência): {Fore.RED}{resistance[0]}{Style.RESET_ALL} (Vol: {resistance[1]:.2f}) - Dist: {dist_r:.2f}%")
            else:
                print(f"    Parede de Venda: {Fore.BLACK}Não detectada (Book Fino){Style.RESET_ALL}")
                
            # Tactical Suggestion
            if obi > 0.2 and trend == "🟢 BULLISH":
                print(f"    {Fore.CYAN}SUGESTÃO: Procurar COMPRA em Pullback perto de {support[0] if support else 'EMA'}{Style.RESET_ALL}")
            elif obi < -0.2 and trend == " BEARISH":
                print(f"    {Fore.CYAN}SUGESTÃO: Procurar VENDA em Repique perto de {resistance[0] if resistance else 'EMA'}{Style.RESET_ALL}")
            else:
                print(f"    {Fore.YELLOW}SUGESTÃO: Aguardar definição (Fluxo vs Tendência divergentes){Style.RESET_ALL}")

        print("\n" + "=" * 70)

if __name__ == "__main__":
    report = HunterReport()
    asyncio.run(report.generate_report())
