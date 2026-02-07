import os
import pandas as pd
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from dotenv import load_dotenv

load_dotenv()

class FireScanner:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.symbols = [
            "SOL_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP", 
            "SUI_USDC_PERP", "HYPE_USDC_PERP", "JUP_USDC_PERP", 
            "WIF_USDC_PERP", "RENDER_USDC_PERP", "PYTH_USDC_PERP"
        ]

    def scan_fire(self):
        print(" FIRE SCANNER: Buscando o Sangue e o Ouro")
        print("===========================================")
        print(f"{'ATIVO':<15} | {'RSI (15m)':<10} | {'VAR (24h)':<10} | {'STATUS'}")
        print("-" * 60)
        
        candidates = []
        
        for sym in self.symbols:
            try:
                # Klines 15m
                klines = self.data.get_klines(sym, "15m", limit=30)
                if not klines: continue
                
                df = pd.DataFrame(klines)
                df['close'] = df['close'].astype(float)
                
                # RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                # Variação (Ticker)
                ticker = self.data.get_ticker(sym)
                price_change = float(ticker.get('priceChangePercent', 0))
                
                status = "Neutro"
                if rsi < 20: status = " SANGRAMENTO EXTREMO (Oportunidade)"
                elif rsi < 30: status = " Oversold"
                elif rsi > 70: status = " Overbought"
                
                print(f"{sym:<15} | {rsi:>5.1f}      | {price_change:>6.2f}%   | {status}")
                
                if rsi < 25:
                    candidates.append((sym, rsi))
                    
            except Exception as e:
                pass
                
        print("-" * 60)
        
        if candidates:
            print("\n ALERTA DE OPORTUNIDADE (RSI < 25):")
            for c in candidates:
                print(f"    {c[0]}: RSI {c[1]:.1f} (Pronto para Repique Violento?)")
        else:
            print("\n   Nenhum ativo em zona de fogo extremo (<25) ainda.")

if __name__ == "__main__":
    scanner = FireScanner()
    scanner.scan_fire()
