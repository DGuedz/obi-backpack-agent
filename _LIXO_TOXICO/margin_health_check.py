import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def audit_margin_health():
    print(" MARGIN HEALTH CHECK & PRUNING ADVISOR")
    print("========================================")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # 1. Get Collateral
    collateral = data.get_account_collateral()
    # Assuming 'availableToTrade' or similar field
    # The get_account_collateral response structure needs verification, using standard fields.
    # Usually: {'available': '...', 'locked': '...', 'total': '...'}
    # Or just print raw to debug if unsure.
    # Based on previous interactions, get_balances returns asset list. get_account_collateral might be specific.
    # Let's try get_balances('USDC') for available cash.
    balances = data.get_balances()
    usdc = balances.get('USDC', {})
    available_margin = float(usdc.get('available', 0))
    locked_margin = float(usdc.get('locked', 0))
    total_equity = available_margin + locked_margin
    
    print(f" EQUITY TOTAL: ${total_equity:.2f}")
    print(f" AVAILABLE MARGIN: ${available_margin:.2f}")
    print(f" LOCKED MARGIN: ${locked_margin:.2f}")
    
    # 2. Analyze Positions PnL
    positions = data.get_positions()
    open_positions = [p for p in positions if float(p['netQuantity']) != 0]
    
    print(f"\n OPEN POSITIONS ({len(open_positions)}):")
    print(f"{'SYMBOL':<15} {'SIDE':<6} {'SIZE':<10} {'ENTRY':<10} {'MARK':<10} {'PnL ($)':<10} {'ROI':<8}")
    print("-" * 80)
    
    total_unrealized_pnl = 0
    
    candidates_for_pruning = []
    
    for pos in open_positions:
        symbol = pos['symbol']
        side = pos['side']
        qty = float(pos['netQuantity'])
        entry = float(pos['entryPrice'])
        mark = float(pos['markPrice'])
        
        # Calc PnL
        # Long: (Mark - Entry) * Qty
        # Short: (Entry - Mark) * Qty
        if side == "Long":
            pnl = (mark - entry) * abs(qty)
        else:
            pnl = (entry - mark) * abs(qty)
            
        initial_margin = (entry * abs(qty)) / 10 # Assuming 10x leverage
        roi = (pnl / initial_margin) * 100 if initial_margin > 0 else 0
        
        total_unrealized_pnl += pnl
        
        print(f"{symbol:<15} {side:<6} {abs(qty):<10.1f} {entry:<10.4f} {mark:<10.4f} {pnl:<10.2f} {roi:<8.2f}%")
        
        # Pruning Logic:
        # 1. Small Positions with Negative PnL (Dead weight)
        # 2. Stagnant Positions (Low ROI after long time - can't check time easily here, assuming stagnant if ROI near 0)
        # 3. High Risk Losers (ROI < -10%)
        
        if roi < -10:
            candidates_for_pruning.append((symbol, "High Loss", pnl))
        elif abs(pnl) < 0.5 and abs(roi) < 2:
            candidates_for_pruning.append((symbol, "Stagnant/Dust", pnl))
            
    print("-" * 80)
    print(f" TOTAL UNREALIZED PnL: ${total_unrealized_pnl:.2f}")
    
    if available_margin < 50:
        print("\n️ CRITICAL: INSUFFICIENT MARGIN FOR FARMING (< $50)")
        print("   Action Required: Close positions to free up capital.")
        
        if candidates_for_pruning:
            print("\n️ PRUNING RECOMMENDATIONS (To Free Margin):")
            for symbol, reason, pnl in candidates_for_pruning:
                print(f"    CLOSE {symbol}: {reason} (PnL: ${pnl:.2f})")
        else:
            print("   ️ No obvious weak positions. You must choose a strategic cut.")
    else:
        print("\n MARGIN HEALTHY. Farming can proceed.")

if __name__ == "__main__":
    audit_margin_health()
