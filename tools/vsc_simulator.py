import sys
import os
import time
import random
from datetime import datetime

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport
from tools.vsc_transformer import VSCTransformer
from core.book_scanner import BookScanner

class VSCSimulator:
    """
     VSC FORWARD SIMULATOR
    Executa 'Paper Trading' acelerado usando dados reais do livro de ofertas.
    Objetivo: Validar a taxa de acerto (Win Rate) do novo algoritmo VSC.
    """
    
    def __init__(self):
        self.transport = BackpackTransport()
        self.vsc = VSCTransformer()
        self.scanner = BookScanner()
        
        # Simulation State
        self.initial_balance = 600.0  # User input: "tinhamos 600 dolares"
        self.balance = self.initial_balance
        self.positions = [] # [{'symbol', 'entry', 'side', 'size', 'vsc_at_entry'}]
        self.history = [] # Closed trades
        self.leverage = 10
        
        # Config
        self.target_assets = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "DOGE_USDC_PERP"]
        self.min_vsc_entry = 0.5 # Exigente
        self.min_obi_entry = 0.2
        
        print(" VSC SIMULATOR INITIALIZED")
        print(f"   -> Starting Capital: ${self.balance}")
        print(f"   -> Strategy: VSC > {self.min_vsc_entry} & OBI > {self.min_obi_entry}")
        
    def run_simulation(self, duration_seconds=60):
        print(f"\n RUNNING LIVE SIMULATION ({duration_seconds}s)...")
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            elapsed = int(time.time() - start_time)
            print(f"\r⏳ Time: {elapsed}/{duration_seconds}s | PnL: ${self.get_unrealized_pnl():.2f} | Trades: {len(self.history)}", end="")
            
            # 1. Scan & Enter
            for symbol in self.target_assets:
                self.process_symbol(symbol)
                
            # 2. Manage Exits
            self.manage_positions()
            
            time.sleep(2) # Tick Speed
            
        print("\n\n SIMULATION COMPLETE.")
        self.generate_report()
        
    def process_symbol(self, symbol):
        # Fetch Data
        try:
            book = self.transport.get_orderbook_depth(symbol)
            if not book: return
            
            # Indicators
            obi = self.scanner.calculate_obi(book)
            vsc_score, trap_signal, confidence = self.vsc.analyze(book)
            
            # Price
            best_ask = float(book['asks'][0][0])
            best_bid = float(book['bids'][0][0])
            mid_price = (best_ask + best_bid) / 2
            
            # Log Rejection (Educativo)
            if abs(obi) > 0.1: # Só logar se tiver algum interesse mínimo
                if vsc_score < self.min_vsc_entry and abs(vsc_score) < self.min_vsc_entry:
                    print(f"    REJECTED {symbol}: OBI {obi:.2f} OK, but VSC {vsc_score:.2f} too weak.")
                elif trap_signal != "NONE":
                    print(f"   ️ TRAP DETECTED {symbol}: {trap_signal} (VSC {vsc_score:.2f})")
            
            # Entry Logic (Long)
            if obi > self.min_obi_entry and vsc_score > self.min_vsc_entry and trap_signal == "NONE":
                self.open_position(symbol, "Long", best_ask, vsc_score)
                
            # Entry Logic (Short)
            elif obi < -self.min_obi_entry and vsc_score < -self.min_vsc_entry and trap_signal == "NONE":
                self.open_position(symbol, "Short", best_bid, vsc_score)
                
        except Exception as e:
            pass
            
    def open_position(self, symbol, side, price, vsc):
        # Check if already open
        for p in self.positions:
            if p['symbol'] == symbol: return
            
        # Size
        size = 100.0 # Fixed bet size
        qty = size / price
        
        self.positions.append({
            'symbol': symbol,
            'side': side,
            'entry': price,
            'qty': qty,
            'vsc_at_entry': vsc,
            'open_time': time.time()
        })
        # print(f"\n    VIRTUAL ENTRY: {side} {symbol} @ {price} (VSC {vsc:.2f})")
        
    def manage_positions(self):
        # Check current prices and exit if TP/SL hit
        # Scalping: TP 0.4%, SL 0.3%
        for p in self.positions[:]:
            try:
                ticker = self.transport.get_ticker(p['symbol'])
                current_price = float(ticker['lastPrice'])
                
                pnl_pct = 0
                if p['side'] == "Long":
                    pnl_pct = (current_price - p['entry']) / p['entry']
                else:
                    pnl_pct = (p['entry'] - current_price) / p['entry']
                    
                pnl_pct_lev = pnl_pct * self.leverage
                
                # Exit Logic
                close_reason = None
                if pnl_pct_lev > 0.04: # +4% ROI
                    close_reason = "TP_HIT"
                elif pnl_pct_lev < -0.03: # -3% ROI
                    close_reason = "SL_HIT"
                elif (time.time() - p['open_time']) > 30: # Time Exit (30s scalps)
                    close_reason = "TIME_EXIT"
                    
                if close_reason:
                    pnl_usd = pnl_pct * (p['qty'] * p['entry']) * self.leverage # Simple calc
                    self.balance += pnl_usd
                    self.history.append({
                        'symbol': p['symbol'],
                        'pnl': pnl_usd,
                        'reason': close_reason,
                        'vsc': p['vsc_at_entry']
                    })
                    self.positions.remove(p)
                    # print(f"\n    CLOSED {p['symbol']}: ${pnl_usd:.2f} ({close_reason})")
                    
            except:
                pass

    def get_unrealized_pnl(self):
        # Simple estimation
        return 0.0 

    def generate_report(self):
        print(" VSC PROJECTION REPORT")
        print("=" * 60)
        total_trades = len(self.history)
        if total_trades == 0:
            print("   No trades executed in this window.")
            return
            
        wins = [t for t in self.history if t['pnl'] > 0]
        losses = [t for t in self.history if t['pnl'] <= 0]
        
        win_rate = (len(wins) / total_trades) * 100
        total_pnl = sum([t['pnl'] for t in self.history])
        
        print(f"   Total Trades: {total_trades}")
        print(f"   Win Rate:     {win_rate:.1f}%")
        print(f"   Net PnL:      ${total_pnl:.2f}")
        print("-" * 60)
        print("    CONCLUSION: Positive Expectancy" if total_pnl > 0 else "    CONCLUSION: Strategy needs refinement")

if __name__ == "__main__":
    sim = VSCSimulator()
    # Run for 60 seconds to gather a sample
    sim.run_simulation(duration_seconds=45)
