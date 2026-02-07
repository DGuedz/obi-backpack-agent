import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def night_report():
    print(" NIGHT REPORT & LOGGING SYSTEM")
    print("==============================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # Create/Append to Log File
    log_file = "night_harvest.log"
    
    # Snapshot
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get Stats
    balances = data.get_balances()
    usdc = balances.get('USDC', {})
    equity = float(usdc.get('available', 0)) + float(usdc.get('locked', 0))
    
    positions = data.get_positions()
    open_pos = [p for p in positions if float(p['netQuantity']) != 0]
    unrealized_pnl = 0
    for p in open_pos:
        entry = float(p['entryPrice'])
        mark = float(p['markPrice'])
        qty = float(p['netQuantity'])
        if p['side'] == "Long":
            unrealized_pnl += (mark - entry) * abs(qty)
        else:
            unrealized_pnl += (entry - mark) * abs(qty)
            
    # Format Entry
    log_entry = f"[{timestamp}] Equity: ${equity:.2f} | PnL: ${unrealized_pnl:.2f} | Pos: {len(open_pos)}\n"
    
    # Write
    with open(log_file, "a") as f:
        f.write(log_entry)
        
    print(f" Logged: {log_entry.strip()}")
    print(f"   Log File: {os.path.abspath(log_file)}")

if __name__ == "__main__":
    night_report()
