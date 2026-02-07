import sys
import os
import time

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport

def calculate_obi(book):
    try:
        bids = book.get('bids', [])
        asks = book.get('asks', [])
        
        if not bids or not asks:
            return 0.0
            
        # Weighted Depth (Top 10 levels)
        bid_vol = sum([float(b[1]) for b in bids[:10]])
        ask_vol = sum([float(a[1]) for a in asks[:10]])
        
        if (bid_vol + ask_vol) == 0:
            return 0.0
            
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)
    except Exception as e:
        return 0.0

def main():
    transport = BackpackTransport()
    
    print("\n EMERGENCY MONITOR: DIAGNOSING PORTFOLIO HEALTH ")
    print("=" * 60)
    
    # 1. Get Collateral/Margin
    try:
        collateral = transport.get_account_collateral()
        equity = float(collateral.get('equity', 0))
        balance = float(collateral.get('balance', 0))
        avail = float(collateral.get('availableToTrade', 0))
        used = equity - avail
        usage_pct = (used / equity) * 100 if equity > 0 else 0
        
        print(f" ACCOUNT STATUS:")
        print(f"   Equity:      ${equity:.2f}")
        print(f"   Balance:     ${balance:.2f}")
        print(f"   Margin Used: {usage_pct:.1f}%")
        
        # Color Code
        if usage_pct > 80:
            print("   STATUS:       CRITICAL (Liquidation Risk High)")
        elif usage_pct > 60:
            print("   STATUS:      🟡 WARNING (High Leverage)")
        else:
            print("   STATUS:      🟢 STABLE")
            
    except Exception as e:
        print(f" Error fetching account data: {e}")
        return

    # 2. Get Positions
    try:
        positions = transport.get_positions()
    except AttributeError:
        # Fallback if method name is different in this version of transport
        positions = transport.get_open_positions() if hasattr(transport, 'get_open_positions') else []
        
    if not positions:
        print("\n No open positions. Capital is safe.")
        return

    print(f"\n POSITION DIAGNOSIS (HOLD vs CUT):")
    print(f"{'SYMBOL':<15} | {'SIDE':<5} | {'PNL($)':<8} | {'OBI':<6} | {'ACTION RECOMMENDATION'}")
    print("-" * 80)
    
    total_risk_score = 0
    total_exposure = 0
    
    for p in positions:
        symbol = p.get('symbol', 'UNKNOWN')
        
        # Quantity & Side Logic
        raw_qty = p.get('quantity')
        if raw_qty is None: raw_qty = p.get('netQuantity', 0)
        quantity = float(raw_qty)
        
        if quantity == 0: continue
        
        side = "Long" if quantity > 0 else "Short"
        
        # Price & PnL Logic
        entry = float(p.get('entryPrice', 0))
        mark_price = float(p.get('markPrice', 0))
        
        pnl = 0
        if entry > 0:
            if side == "Long":
                pnl = (mark_price - entry) * abs(quantity)
            else:
                pnl = (entry - mark_price) * abs(quantity)
        
        # Check if API provides PnL directly (override calculation if better)
        if 'unrealizedPnl' in p:
            pnl = float(p['unrealizedPnl'])
            
        position_value = mark_price * abs(quantity)
        total_exposure += position_value
        
        # Get OBI
        book = transport.get_orderbook_depth(symbol)
        obi = calculate_obi(book)
        
        # Analyze Divergence
        recommendation = "HOLD "
        risk_level = 0
        
        if side == "Long":
            if obi < -0.2:
                recommendation = "CUT ️ (Bearish Book)"
                risk_level = 2
            elif obi < 0:
                recommendation = "WATCH  (Weak)"
                risk_level = 1
            else:
                recommendation = "HOLD  (Bullish Book)"
        else: # Short
            if obi > 0.2:
                recommendation = "CUT ️ (Bullish Book)"
                risk_level = 2
            elif obi > 0:
                recommendation = "WATCH  (Weak)"
                risk_level = 1
            else:
                recommendation = "HOLD  (Bearish Book)"
        
        total_risk_score += risk_level
        print(f"{symbol:<15} | {side:<5} | {pnl:<8.2f} | {obi:<6.2f} | {recommendation}")
        
    print("-" * 80)
    
    # 3. Scenario Analysis
    print(f"\n SCENARIO ANALYSIS:")
    print(f"   Total Exposure: ${total_exposure:.2f}")
    if total_exposure > 0:
        leverage = total_exposure / equity if equity > 0 else 999
        print(f"   Real Leverage:  {leverage:.2f}x")
        
        # Estimate Liquidation Drop
        # If Equity drops to ~50% of Margin Used (Approx Maintenance), we die.
        # Let's assume Maintenance Margin is ~50% of 'used' (which is Initial Margin).
        maintenance_margin = used * 0.5 
        buffer = equity - maintenance_margin
        drop_capacity_pct = (buffer / total_exposure) * 100
        
        print(f"   Est. Buffer:    ${buffer:.2f}")
        print(f"   Max Drop (%):   ~{drop_capacity_pct:.2f}% (Market Move to Liquidation)")
        
        if drop_capacity_pct < 5:
            print("\n URGENT: Portfolio cannot withstand a 5% drop.")
            print("   ACTION: Reduce leverage immediately.")
    
    if total_risk_score >= 3:
        print("\n️  STRATEGY ALERT: Multiple positions are fighting the order book.")
        print("    The 'Bull Trap' scenario is confirmed by Order Book Imbalance.")

if __name__ == "__main__":
    main()
