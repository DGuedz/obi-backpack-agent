import os
import sys
from dotenv import load_dotenv
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
from core.backpack_transport import BackpackTransport

def check_pnl():
    transport = BackpackTransport()
    positions = transport.get_positions()
    
    print(f"\n REAL-TIME PNL CHECK")
    print(f"{'SYMBOL':<15} | {'SIDE':<5} | {'ENTRY':<10} | {'MARK':<10} | {'PNL($)':<8} | {'ROI(%)':<8}")
    print("-" * 75)
    
    for p in positions:
        symbol = p['symbol']
        # Fix Quantity logic
        raw_qty = p.get('quantity')
        if raw_qty is None: raw_qty = p.get('netQuantity', 0)
        qty = float(raw_qty)
        
        if qty == 0: continue
        
        side = "Long" if qty > 0 else "Short"
        entry = float(p.get('entryPrice', 0))
        mark = float(p.get('markPrice', 0))
        leverage = 10 # Assumed based on system config
        
        pnl = 0
        roi = 0
        
        if entry > 0:
            if side == "Long":
                pnl = (mark - entry) * abs(qty)
                roi = ((mark - entry) / entry) * leverage * 100
            else:
                pnl = (entry - mark) * abs(qty)
                roi = ((entry - mark) / entry) * leverage * 100
                
        print(f"{symbol:<15} | {side:<5} | {entry:<10.4f} | {mark:<10.4f} | {pnl:<8.2f} | {roi:<8.2f}%")
    
    print("-" * 75)

    # Check JUP history
    print("\n️ JUPITER (JUP) STATUS CHECK:")
    history = transport.get_fill_history(limit=50, symbol="JUP_USDC_PERP")
    if history:
        last_fill = history[0]
        print(f"   Last Fill: {last_fill.get('side')} {last_fill.get('quantity')} @ {last_fill.get('price')} (Time: {last_fill.get('timestamp')})")
    else:
        print("   No recent history found.")

if __name__ == "__main__":
    check_pnl()
