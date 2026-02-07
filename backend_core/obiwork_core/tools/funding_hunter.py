
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

class FundingHunter:
    """
     FUNDING HUNTER
    Analisa Taxas de Financiamento (Funding Rates) para identificar:
    1. Short Squeezes (Funding Negativo + OBI Comprador)
    2. Trend Continuation (Funding Positivo + OBI Comprador)
    3. Yield Farming (Delta Neutral Opportunities - Not implemented yet)
    """
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data)
        
    async def analyze(self):
        print(f"\n{Style.BRIGHT}OBIWORK FUNDING HUNTER - Data Science Mode{Style.RESET_ALL}")
        print("=" * 80)
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'FUNDING (1h)':<15} | {'OBI':<10} | {'STATUS':<15}")
        print("-" * 80)
        
        # 1. Fetch Mark Prices (Funding Data)
        try:
            mark_prices = self.data.get_mark_prices()
        except Exception as e:
            print(f"[ERROR] Fetch Mark Prices Failed: {e}")
            return

        if not mark_prices:
            print("[ERROR] No Funding Data Found.")
            return

        # 2. Parse and Sort
        opportunities = []
        for mp in mark_prices:
            symbol = mp.get('symbol')
            if not symbol.endswith('_PERP'): continue
            
            funding = float(mp.get('fundingRate', 0))
            price = float(mp.get('markPrice', 0))
            
            opportunities.append({
                'symbol': symbol,
                'funding': funding,
                'price': price,
                'abs_funding': abs(funding)
            })
            
        # Sort by Absolute Funding (High Impact)
        opportunities.sort(key=lambda x: x['abs_funding'], reverse=True)
        
        # 3. Deep Analysis on Top Candidates (Expanded to 30)
        top_candidates = opportunities[:30]
        
        results = []
        
        for opp in top_candidates:
            symbol = opp['symbol']
            funding = opp['funding']
            price = opp['price']
            
            # Fetch Depth for OBI
            depth = self.data.get_orderbook_depth(symbol)
            obi = self.oracle.calculate_obi(depth)
            
            # Determine Status
            funding_pct = funding * 100
            status = "NEUTRAL"
            color = Fore.WHITE
            
            # Score Calculation for Ranking
            score = abs(funding) * 1000 + abs(obi)
            
            if funding < -0.0002: # Funding Negativo Forte (-0.02%)
                if obi > 0.05:
                    status = "LONG SQUEEZE" # Shorts pagando Longs + Pressão de Compra
                    color = Fore.GREEN
                    score += 5 # Bonus
                else:
                    status = "BEAR HEAVY" # Shorts pagando, mas OBI ainda vendedor
                    color = Fore.RED
            elif funding > 0.0002: # Funding Positivo Forte
                if obi < -0.05:
                    status = "SHORT SQUEEZE" # Longs pagando Shorts + Pressão de Venda
                    color = Fore.RED
                    score += 5
                else:
                    status = "BULL HEAVY" # Longs pagando, OBI comprador (Tendência forte)
                    color = Fore.GREEN
            
            print(f"{color}{symbol:<15} | ${price:<9.4f} | {funding_pct:>8.4f}%      | {obi:>5.2f}      | {status}{Style.RESET_ALL}")
            
            opp['obi'] = obi
            opp['score'] = score
            results.append(opp)
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.05)
            
        print("=" * 80)
        print(f"{Fore.CYAN}INFO: Negative Funding = Shorts pay Longs. Positive Funding = Longs pay Shorts.{Style.RESET_ALL}")
        
        # Return ranked by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

if __name__ == "__main__":
    hunter = FundingHunter()
    asyncio.run(hunter.analyze())
