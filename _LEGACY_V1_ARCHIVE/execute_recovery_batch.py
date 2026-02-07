import os
import sys
import time
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from safe_execution import SafeExecutor
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

# --- CONFIG ---
LEVERAGE = 50
STOP_LOSS_PCT = 1.0 # 1% SL for 50x = 50% Loss Risk (High but Recovery Mode)
CAPITAL_ALLOCATION = 0.70 # 70% of available margin

def execute_recovery_protocol():
    print(f"\n️ [RECOVERY PROTOCOL ACTIVATED] EXECUTION MODE: 50X")
    print("   ️ TARGETS: PAXG_USDC_PERP (SHORT) & SOL_USDC_PERP (LONG)")
    print("   ️ ATOMIC PROTECTION: ON (1% Hard Stop)")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Calculate Position Size
    # We split the 70% capital between the two assets (35% each)
    balances = data.get_balances()
    usdc_balance = 0.0
    if 'USDC' in balances:
        usdc_balance = float(balances['USDC']['available'])
        
    print(f"    Available Capital: ${usdc_balance:.2f}")
    
    if usdc_balance < 10:
        print("    Insufficient funds for recovery operation.")
        return

    deploy_capital = usdc_balance * CAPITAL_ALLOCATION
    per_trade_capital = deploy_capital / 2
    
    print(f"    Deploying ${deploy_capital:.2f} total (${per_trade_capital:.2f} per trade)")
    
    # --- EXECUTION 1: PAXG SHORT ---
    symbol = "PAXG_USDC_PERP"
    print(f"\n   1️⃣ EXECUTING {symbol} SHORT...")
    try:
        trade.set_leverage(symbol, LEVERAGE)
        
        ticker = data.get_ticker(symbol)
        price = float(ticker['lastPrice'])
        
        # Quantity calculation: (Margin * Leverage) / Price
        qty = (per_trade_capital * LEVERAGE) / price
        qty = round(qty, 3) # PAXG Precision
        
        executor = SafeExecutor(symbol)
        # Atomic Entry
        executor.execute_atomic_order("Sell", qty, LEVERAGE, sl_pct=STOP_LOSS_PCT/100)
        
    except Exception as e:
        print(f"    FAILED {symbol}: {e}")
        
    # --- EXECUTION 2: SOL LONG ---
    symbol = "SOL_USDC_PERP"
    print(f"\n   2️⃣ EXECUTING {symbol} LONG...")
    try:
        trade.set_leverage(symbol, LEVERAGE)
        
        ticker = data.get_ticker(symbol)
        price = float(ticker['lastPrice'])
        
        # Quantity calculation
        qty = (per_trade_capital * LEVERAGE) / price
        qty = round(qty, 1) # SOL Precision usually 1 decimal or 0
        if qty < 0.1: qty = 0.1
        
        executor = SafeExecutor(symbol)
        # Atomic Entry
        executor.execute_atomic_order("Buy", qty, LEVERAGE, sl_pct=STOP_LOSS_PCT/100)
        
    except Exception as e:
        print(f"    FAILED {symbol}: {e}")
        
    print("\n RECOVERY BATCH COMPLETE. MONITORING VIA SENTINEL & PROFIT LOCK.")

if __name__ == "__main__":
    execute_recovery_protocol()
