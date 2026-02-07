import os
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators
from smart_entry import SmartEntrySniper

# Load Environment
load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)
indicators = BackpackIndicators()

# Target List (Non-Toxic Alts)
ALTS = [
    "SOL_USDC_PERP", 
    "ETH_USDC_PERP", 
    "SUI_USDC_PERP", 
    "DOGE_USDC_PERP", 
    "AVAX_USDC_PERP", 
    "LINK_USDC_PERP",
    "JUP_USDC_PERP"
]

print("\n SCANNING NON-TOXIC ALTS FOR SNIPER ENTRY...")
print("==============================================")
print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'TREND':<10} | {'RSI':<6} | {'SIGNAL':<10} | {'REASON'}")
print("-" * 100)

for symbol in ALTS:
    try:
        sniper = SmartEntrySniper(symbol, data, trade, indicators)
        signal, reason, rsi, ema_200, price = sniper.analyze()
        
        trend = "BULL 🟢" if price > ema_200 else "BEAR "
        sig_str = f" {signal}" if signal else " WAIT"
        
        print(f"{symbol:<15} | {price:<10.4f} | {trend:<10} | {rsi:<6.2f} | {sig_str:<10} | {reason}")
    except Exception as e:
        print(f"{symbol:<15} | ERROR: {e}")

print("==============================================")
