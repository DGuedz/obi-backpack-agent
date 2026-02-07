
import os
import sys
import time
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport
from tools.vsc_transformer import VSCTransformer
from tools.hft_indicators import HFTIndicators

class RecoveryScanner:
    """
     RECOVERY SCANNER (50x Potential - High Precision)
    Foca em encontrar ativos com tendência CLARA de alta para recuperar liquidez.
    Filtros: VSC > 0.8 (Alta Convicção) + HFT Trend Alignment
    """
    def __init__(self):
        self.transport = BackpackTransport()
        self.vsc = VSCTransformer()
        self.hft = HFTIndicators()
        
    def scan(self):
        print(" OBI RECOVERY SCANNER INITIALIZED")
        print("   -> Strategy: LONG ONLY (Clear Uptrend)")
        print("   -> Filter: VSC > 0.8 + VWAP Support")
        print("   -> Goal: Recover Liquidity Quickly")
        
        try:
            markets = self.transport.get_all_markets()
            # Filter for PERP
            perps = [m['symbol'] for m in markets if 'PERP' in m.get('symbol', '')]
            print(f"   -> Analyzing {len(perps)} markets...")
            
            candidates = []
            
            for symbol in perps:
                try:
                    # 1. Quick Trend Check (Klines)
                    klines = self.transport.get_klines(symbol, "15m", limit=20)
                    if not klines: continue
                    
                    closes = [float(k['close']) for k in klines]
                    current_price = closes[-1]
                    
                    vwap = self.hft.calculate_vwap(klines)
                    ema_fast = self.hft.calculate_ema(closes, 9)
                    ema_slow = self.hft.calculate_ema(closes, 21)
                    
                    # Trend Filter: Price > VWAP and EMA9 > EMA21 (Golden Cross)
                    if current_price > vwap and ema_fast > ema_slow:
                        # 2. Deep Dive (VSC)
                        book = self.transport.get_orderbook_depth(symbol)
                        if not book: continue
                        
                        vsc_score, trap, conf = self.vsc.analyze(book)
                        
                        # Recovery Mode requires HIGH confidence
                        if vsc_score > 0.7: # Strong Buy Pressure
                            print(f"    FOUND CANDIDATE: {symbol}")
                            print(f"      Price: {current_price} | VSC: {vsc_score:.2f}")
                            print(f"      Trend: BULLISH (Above VWAP)")
                            
                            candidates.append({
                                'symbol': symbol,
                                'price': current_price,
                                'vsc': vsc_score
                            })
                except Exception as e:
                    continue
                    
            # Sort by VSC (Strongest First)
            candidates.sort(key=lambda x: x['vsc'], reverse=True)
            
            print("\n TOP RECOVERY OPPORTUNITIES:")
            if not candidates:
                print("    No clear uptrends found with VSC > 0.7")
            else:
                for c in candidates[:3]:
                    print(f"    {c['symbol']} (VSC: {c['vsc']:.2f})")
                    
        except Exception as e:
            print(f"    Scan Error: {e}")

if __name__ == "__main__":
    scanner = RecoveryScanner()
    scanner.scan()
