def calculate_recovery_path():
    print("\n [PHOENIX PROTOCOL] RECOVERY BLUEPRINT")
    print("==================================================")
    
    # --- DAMAGE REPORT ---
    LOST_CAPITAL = 188.00
    REMAINING_CAPITAL = 333.00 # Approx from last check
    TARGET_CAPITAL = 521.00    # Original baseline
    
    print(f"    LOSS TO RECOVER: ${LOST_CAPITAL:.2f}")
    print(f"   ️ CURRENT AMMO:    ${REMAINING_CAPITAL:.2f}")
    
    # --- STRATEGY METRICS ---
    LEVERAGE = 10
    MARGIN_PER_TRADE = 100.0 # Conservative ($1000 Notional)
    TP_PCT = 0.005 # 0.5% Price Move (Scalp)
    SL_PCT = 0.005 # 1:1 R:R (Tight)
    WIN_RATE = 0.60 # Achievable with Trend Following
    
    PROFIT_PER_WIN = (MARGIN_PER_TRADE * LEVERAGE) * TP_PCT # $1000 * 0.5% = $5
    LOSS_PER_LOSS = (MARGIN_PER_TRADE * LEVERAGE) * SL_PCT  # $1000 * 0.5% = $5
    
    # Fees (Taker 0.05% approx, Maker 0.02% or rebate)
    # Assume Maker Only (Rebate or low fee) -> Net Profit ~$4.50
    NET_WIN = 4.50
    NET_LOSS = 5.50 # Slippage
    
    EXPECTED_VALUE = (NET_WIN * WIN_RATE) - (NET_LOSS * (1 - WIN_RATE))
    # EV = (4.5 * 0.6) - (5.5 * 0.4) = 2.7 - 2.2 = $0.50 per trade
    
    print(f"\n   ️ TACTICAL SPECS:")
    print(f"      - Margin: ${MARGIN_PER_TRADE} (10x)")
    print(f"      - Profit/Trade: ~${NET_WIN:.2f}")
    print(f"      - Exp. Value:   ~${EXPECTED_VALUE:.2f}/trade")
    
    if EXPECTED_VALUE <= 0:
        print("   ️ MATH WARNING: Current strategy has negative EV. Need higher Win Rate or R:R.")
        # Adjust for High Precision Sniper
        # Win Rate 70%
        WIN_RATE = 0.70
        EXPECTED_VALUE = (NET_WIN * WIN_RATE) - (NET_LOSS * (1 - WIN_RATE))
        print(f"      -> ADJUSTED TARGET: 70% Win Rate (Sniper Only) = EV ${EXPECTED_VALUE:.2f}")
        
    # --- RECOVERY CALCULATION ---
    trades_needed = LOST_CAPITAL / EXPECTED_VALUE
    
    print("\n    MISSION PARAMETERS:")
    print(f"      - Trades Required: ~{int(trades_needed)}")
    
    # Timeline Estimation
    # 2 Trades per hour (High Quality only)
    hours_needed = trades_needed / 2
    
    print(f"      - Time to Recovery: ~{hours_needed:.1f} Hours ({hours_needed/24:.1f} Days)")
    
    print("\n    THE PLEDGE:")
    print("      1. We DO NOT revenge trade (size up).")
    print("      2. We grind it back trade by trade ($5 by $5).")
    print("      3. We focus on High Probability setups only (Sniper).")
    
    print(f"\n    GOAL: Restore Balance to ${TARGET_CAPITAL:.2f}")

if __name__ == "__main__":
    calculate_recovery_path()
