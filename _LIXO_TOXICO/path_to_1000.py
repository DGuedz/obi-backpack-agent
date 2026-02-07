def calculate_path_to_glory():
    print("\n [PATH TO $1000] COMPOUND GROWTH SIMULATION")
    print("==================================================")
    
    # --- STARTING POINT ---
    START_CAPITAL = 333.00
    TARGET = 1000.00
    
    print(f"    START: ${START_CAPITAL:.2f}")
    print(f"    GOAL:  ${TARGET:.2f} (+{(TARGET-START_CAPITAL)/START_CAPITAL*100:.1f}%)")
    
    # --- STRATEGY: THE SNIPER COMPOUND ---
    # We need to grow aggressive but safe.
    # Daily Goal: 5% (Very aggressive but possible with 10x)
    # 5% of $333 = $16.
    
    DAILY_GROWTH_TARGET = 0.05 # 5% per day
    TRADES_PER_DAY = 3
    WIN_RATE = 0.70 # Must be high quality
    
    current_balance = START_CAPITAL
    days = 0
    
    print(f"\n    GROWTH PROJECTION (Daily Target: {DAILY_GROWTH_TARGET*100}%):")
    print(f"   {'DAY':<5} | {'BALANCE':<10} | {'PROFIT':<10}")
    print("-" * 35)
    
    while current_balance < TARGET:
        days += 1
        daily_profit = current_balance * DAILY_GROWTH_TARGET
        current_balance += daily_profit
        
        print(f"   {days:<5} | ${current_balance:<10.2f} | +${daily_profit:<10.2f}")
        
        if days > 100: # Safety break
            print("   ... (Too slow)")
            break
            
    print("-" * 35)
    print(f"\n    GOAL REACHED IN {days} DAYS.")
    
    # --- TACTICAL REQUIREMENTS ---
    print("\n   ️ DAILY REQUIREMENTS:")
    req_profit = START_CAPITAL * DAILY_GROWTH_TARGET # $16
    print(f"      - Net Profit Needed Today: ${req_profit:.2f}")
    print(f"      - Trades: {TRADES_PER_DAY} wins of ${req_profit/TRADES_PER_DAY:.2f}")
    print(f"      - Leverage: 10x")
    print(f"      - Position Size: Dynamic (Use full available margin safely)")

if __name__ == "__main__":
    calculate_path_to_glory()
