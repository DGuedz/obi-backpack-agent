import os
import sys
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

class OBIValidator:
    def __init__(self, symbols=['BTC_USDC_PERP', 'SOL_USDC_PERP'], duration=60, interval=10):
        self.symbols = symbols
        self.duration = duration
        self.interval = interval
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data)
        self.transport = BackpackTransport()
        
        self.results = []

    async def run(self):
        print(f"\n{Style.BRIGHT} OBI THESIS VALIDATOR (Live Simulation)")
        print(f"⏱️ Duration: {self.duration}s | Interval: {self.interval}s")
        print("=" * 80)
        
        start_time = time.time()
        
        while (time.time() - start_time) < self.duration:
            print(f"\nScanning snapshot @ {time.strftime('%H:%M:%S')}...")
            
            tasks = [self._test_prediction(s) for s in self.symbols]
            iteration_results = await asyncio.gather(*tasks)
            
            self.results.extend(iteration_results)
            
            # Wait for next cycle (minus execution time)
            await asyncio.sleep(self.interval)

        self._print_summary()

    async def _test_prediction(self, symbol):
        # 1. Capture State T0
        depth = self.data.get_orderbook_depth(symbol)
        ticker = self.transport.get_ticker(symbol)
        
        if not depth or not ticker: return None
        
        price_t0 = float(ticker['lastPrice'])
        obi = self.oracle.calculate_obi(depth)
        
        # 2. Predict
        prediction = "NEUTRAL"
        if obi > 0.25: prediction = "UP"
        elif obi < -0.25: prediction = "DOWN"
        
        if prediction == "NEUTRAL":
            print(f"   {symbol}: OBI {obi:.2f} (Neutral) - Skipping prediction")
            return {'symbol': symbol, 'obi': obi, 'result': 'SKIPPED'}
            
        print(f"   {symbol}: OBI {obi:.2f} -> Predicting {prediction} (Price: {price_t0})")
        
        # 3. Wait for Outcome (Micro-Simulação de 5s dentro do ciclo)
        await asyncio.sleep(5)
        
        # 4. Capture State T1
        ticker_t1 = self.transport.get_ticker(symbol)
        price_t1 = float(ticker_t1['lastPrice'])
        
        delta_pct = (price_t1 - price_t0) / price_t0 * 100
        
        # 5. Validate
        is_correct = False
        if prediction == "UP" and price_t1 > price_t0: is_correct = True
        elif prediction == "DOWN" and price_t1 < price_t0: is_correct = True
        
        result_color = Fore.GREEN if is_correct else Fore.RED
        result_str = "WIN" if is_correct else "LOSS"
        
        print(f"     -> T1 Price: {price_t1} ({delta_pct:.4f}%) | Result: {result_color}{result_str}{Style.RESET_ALL}")
        
        return {
            'symbol': symbol,
            'obi': obi,
            'prediction': prediction,
            'delta': delta_pct,
            'result': result_str
        }

    def _print_summary(self):
        print(f"\n{Style.BRIGHT} VALIDATION RESULTS SUMMARY")
        print("=" * 80)
        
        valid_samples = [r for r in self.results if r and r['result'] != 'SKIPPED']
        if not valid_samples:
            print("️ No strong signals detected during simulation window.")
            return
            
        wins = len([r for r in valid_samples if r['result'] == 'WIN'])
        total = len(valid_samples)
        win_rate = (wins / total) * 100
        
        print(f"Total Predictions: {total}")
        print(f"Correct Predictions: {wins}")
        print(f"Hit Rate: {Fore.YELLOW if win_rate < 50 else Fore.GREEN}{win_rate:.1f}%{Style.RESET_ALL}")
        
        avg_obi_win = sum([abs(r['obi']) for r in valid_samples if r['result'] == 'WIN']) / wins if wins > 0 else 0
        print(f"Avg OBI Strength on Wins: {avg_obi_win:.2f}")

if __name__ == "__main__":
    validator = OBIValidator()
    asyncio.run(validator.run())
