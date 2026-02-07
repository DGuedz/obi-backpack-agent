import pandas as pd

def project_earnings():
    print("\n [ORACLE PROJECTION] 6:00 AM FORECAST")
    print("==================================================")
    
    # --- INPUTS ---
    CURRENT_EQUITY = 514.54 # From last check
    HOURS_REMAINING = 7.5   # 22:30 to 06:00
    
    # Grid Metrics (Conservative)
    GRID_TRADES_PER_HOUR = 4 # 2 round trips
    GRID_NOTIONAL = 1000.0   # Scaled down size
    GRID_WIN_PCT = 0.70      # User Scenario
    GRID_AVG_WIN_PCT = 0.005 # 0.5% (TP Target)
    GRID_AVG_LOSS_PCT = 0.008 # 0.8% (Stop/Scratch)
    
    # Sniper Metrics (Opportunity)
    SNIPER_SHOTS = 2         # Est. setups per night
    SNIPER_NOTIONAL = 2000.0 # Heavy Artillery
    SNIPER_WIN_PCT = 0.70
    SNIPER_AVG_WIN_PCT = 0.03 # 3% (Trend Move)
    SNIPER_AVG_LOSS_PCT = 0.015 # 1.5% (Sentinel Stop)
    
    # --- CALCULATION ---
    
    # 1. Weaver Grid (Volume Machine)
    total_grid_trades = int(GRID_TRADES_PER_HOUR * HOURS_REMAINING)
    grid_wins = int(total_grid_trades * GRID_WIN_PCT)
    grid_losses = total_grid_trades - grid_wins
    
    grid_profit = grid_wins * (GRID_NOTIONAL * GRID_AVG_WIN_PCT)
    grid_loss = grid_losses * (GRID_NOTIONAL * GRID_AVG_LOSS_PCT)
    grid_net = grid_profit - grid_loss
    grid_volume = total_grid_trades * GRID_NOTIONAL
    
    # 2. Hunter Killer (Sniper)
    sniper_wins = SNIPER_SHOTS * SNIPER_WIN_PCT # Expected value
    sniper_losses = SNIPER_SHOTS * (1 - SNIPER_WIN_PCT)
    
    sniper_profit = sniper_wins * (SNIPER_NOTIONAL * SNIPER_AVG_WIN_PCT)
    sniper_loss = sniper_losses * (SNIPER_NOTIONAL * SNIPER_AVG_LOSS_PCT)
    sniper_net = sniper_profit - sniper_loss
    sniper_volume = SNIPER_SHOTS * SNIPER_NOTIONAL
    
    # 3. Aggregated Result
    total_net_profit = grid_net + sniper_net
    projected_equity = CURRENT_EQUITY + total_net_profit
    total_volume = grid_volume + sniper_volume
    
    # --- OUTPUT ---
    print(f" SCENARIO: 70% Win Rate | {HOURS_REMAINING} Hours")
    print(f"-" * 50)
    print(f"️ GRID PERFORMANCE (Est. {total_grid_trades} trades):")
    print(f"   - Wins: {grid_wins} | Losses: {grid_losses}")
    print(f"   - Net PnL: ${grid_net:+.2f}")
    print(f"   - Volume:  ${grid_volume:,.2f}")
    
    print(f"\n SNIPER PERFORMANCE (Est. {SNIPER_SHOTS} shots):")
    print(f"   - Net PnL: ${sniper_net:+.2f}")
    print(f"   - Volume:  ${sniper_volume:,.2f}")
    
    print(f"=" * 50)
    print(f" PROJECTED PROFIT:   ${total_net_profit:+.2f}")
    print(f" PROJECTED EQUITY:   ${projected_equity:,.2f}")
    print(f" TOTAL VOLUME 24H:   +${total_volume:,.2f}")
    print(f"=" * 50)
    
    roi = (total_net_profit / CURRENT_EQUITY) * 100
    print(f" EST. NIGHT ROI:     {roi:+.2f}%")

if __name__ == "__main__":
    project_earnings()
