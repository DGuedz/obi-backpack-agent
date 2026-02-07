
import os
import time
import sys
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminho para importar módulos legados
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from pre_flight_checklist import UltimateChecklist

# Config
LEVERAGE = 50
TARGET_ROE = 30 # % (Lucro Alvo)
STOP_LOSS_ROE = 50 # % (Stop Loss baseado em ROE, 1% Price Move * 50x = 50% ROE)
CAPITAL_ALLOCATION = 0.70 # 70% do Capital Disponível

# ROE Formula: ROE = PriceMove% * Leverage
# Target Price Move = 30% / 50 = 0.6%
# Stop Price Move = 50% / 50 = 1.0%

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def scan_market():
    print(f" DEEP OPPORTUNITY SCANNER (50x | 70% Cap)")
    print(f"   Target: +0.6% Move (+30% ROE) | Stop: -1.0% Move (-50% ROE)")
    print("==================================================")
    
    # 1. Get Tickers (Liquidity Filter)
    tickers = data.get_tickers()
    if not tickers:
        print(" Failed to fetch tickers.")
        return

    # Filter Liquid Pairs (USDC Perps only)
    candidates = []
    for t in tickers:
        if 'USDC' in t['symbol'] and float(t['volume']) > 1000000: # Min $1M Volume
             candidates.append(t)
             
    print(f" Analyzing {len(candidates)} liquid assets...")
    
    # 2. Analyze Candidates
    for t in candidates:
        symbol = t['symbol']
        price = float(t['lastPrice'])
        
        # Instantiate Checklist for THIS symbol
        try:
            checklist = UltimateChecklist(symbol)
        except Exception as e:
            print(f"   ️ Error initializing checklist for {symbol}: {e}")
            continue
        
        # Funding Check (Basic)
        # funding = float(t.get('fundingRate', 0))
        
        # 3. Run 5-Layer Checklist
        # We test both Long and Short scenarios
        
        # Test LONG
        print(f"\n   Checking {symbol} (LONG)...")
        approved_long, reason_long = checklist.run_full_scan(side="Buy", leverage=LEVERAGE, balance=100) # Dummy balance for check
        
        if approved_long:
            print(f"    [LONG APPROVED] {symbol}")
            print(f"      Entry: {price}")
            print(f"      TP: {price * 1.006:.4f} (+0.6%)")
            print(f"      SL: {price * 0.99:.4f} (-1.0%)")
            print(f"      Reason: {reason_long}")
            
        # Test SHORT
        # print(f"   Checking {symbol} (SHORT)...")
        approved_short, reason_short = checklist.run_full_scan(side="Sell", leverage=LEVERAGE, balance=100)
        
        if approved_short:
             print(f"    [SHORT APPROVED] {symbol}")
             print(f"      Entry: {price}")
             print(f"      TP: {price * 0.994:.4f} (-0.6%)")
             print(f"      SL: {price * 1.01:.4f} (+1.0%)")
             print(f"      Reason: {reason_short}")
             
        if not approved_long and not approved_short:
            # print(f"       Rejected: {reason_long}")
            pass

if __name__ == "__main__":
    scan_market()
