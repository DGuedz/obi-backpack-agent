import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

try:
    from backpack_transport import BackpackTransport
    from backpack_data import BackpackData
    from backpack_auth import BackpackAuth
    from technical_oracle import TechnicalOracle
except ImportError as e:
    print(f" Import Error: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("SmartMoneyScanner")

class SmartMoneyScanner:
    def __init__(self):
        load_dotenv()
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        
    async def scan_market(self):
        print(" STARTING SMART MONEY SCAN (OBI & WHALE WALLS)...")
        print("-" * 60)
        
        # 1. Get Markets
        markets = self.data_client.get_markets()
        if not markets:
            print(" Error fetching markets.")
            return

        # Filter USDC Perpetuals
        perp_symbols = [m['symbol'] for m in markets if 'USDC_PERP' in m['symbol']]
        
        results = []
        
        print(f" Analyzing {len(perp_symbols)} assets for institutional flow...")
        
        for symbol in perp_symbols:
            try:
                # Get Depth and Ticker
                depth = self.data_client.get_orderbook_depth(symbol)
                ticker = self.transport.get_ticker(symbol)
                
                if not depth or not ticker:
                    continue
                    
                # Calculate OBI (Order Book Imbalance)
                obi = self.oracle.calculate_obi(depth)
                
                # Identify Whale Walls
                # Simple heuristic: If Top 5 Bids Volume is 3x larger than Top 5 Asks (or vice-versa)
                bids_vol = sum([float(b[1]) for b in depth['bids'][:5]])
                asks_vol = sum([float(a[1]) for a in depth['asks'][:5]])
                
                wall_ratio = 0
                wall_side = "Neutral"
                
                if asks_vol > 0:
                    ratio_bid = bids_vol / asks_vol
                    if ratio_bid > 2.0:
                        wall_side = "BUY (Bid Wall)"
                        wall_ratio = ratio_bid
                    elif ratio_bid < 0.5:
                        wall_side = "SELL (Ask Wall)"
                        wall_ratio = 1 / ratio_bid
                
                # 24h Volume (Liquidity)
                vol_24h = float(ticker['volume']) * float(ticker['lastPrice']) # Approx USD
                
                # Filter only relevant assets or anomalies
                # Strong OBI (>0.25 or <-0.25) OR Wall detected
                if abs(obi) > 0.25 or wall_ratio > 2.0:
                    results.append({
                        'symbol': symbol,
                        'price': float(ticker['lastPrice']),
                        'obi': obi,
                        'wall_side': wall_side,
                        'wall_strength': wall_ratio,
                        'vol_24h': vol_24h
                    })
                    
            except Exception as e:
                pass
                # print(f"Error in {symbol}: {e}")

        # Sort by OBI Strength (Absolute)
        results.sort(key=lambda x: abs(x['obi']), reverse=True)
        return results

if __name__ == "__main__":
    scanner = SmartMoneyScanner()
    asyncio.run(scanner.scan_market())
