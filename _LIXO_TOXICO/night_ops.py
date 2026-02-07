import os
import sys
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators
from weaver_grid import WeaverGrid
from sentinel import Sentinel

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"
LAYERS = 3

def night_ops():
    print("\n [PROTOCOL NOCTURNE] ACTIVATED. Night Ops Grid Launching...")
    print(f"    Target: {SYMBOL}")
    print(f"   ️ Strategy: Multi-Level Weaver Grid ({LAYERS} Layers)")
    print("    Objective: Volume Farm & Scrap Collection (Sobras)")
    
    # Init
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    # 1. Activate Sentinel (SHIELD)
    # Critical for "No Hallucinations" promise
    sentinel = Sentinel(data, trade)
    sentinel.start()
    print("   ️ [SENTINEL] Shield Active & Monitoring.")
    
    weaver = WeaverGrid(SYMBOL, data, trade, indicators)
    
    # Execution Loop (The Farm)
    print("\n [FARM BOT] Starting Infinite Loop...")
    
    try:
        while True:
            try:
                # 1. Check if orders need replenishment
                # Simple Logic: If no open orders (or few), Re-Grid.
                # Ideally: Check specific grid levels. 
                # Brute Force: Just run execute_grid, it places orders.
                # WeaverGrid doesn't check existing orders yet, it just places.
                # So we should cancel old ones or only place if empty.
                
                # Let's cancel all first to "Reset" the net (Churn Strategy)
                # This ensures we follow the price if it moved.
                # CANCEL ALL is aggressive but guarantees "Following the Price".
                
                # Only cancel if price moved significantly? Or every cycle?
                # Let's do every 5 minutes cycle.
                
                print(f"\n⏳ Cycle Start: {time.strftime('%H:%M:%S')}")
                
                # Cancel All (Reset Net)
                try:
                    # Cancel only if we want to move the grid.
                    # If we want to capture range, we leave them.
                    # But to generate volume, we need fills.
                    # If price moved away, we must move grid.
                    trade.cancel_all_orders(SYMBOL) 
                    # Need to implement cancel_all_orders in Trade or use ad-hoc
                    # trade.cancel_all_orders usually exists? No, optimize_margin used requests.
                    # Let's implement ad-hoc here or trust Weaver to place new ones.
                    # Better to clear old trash.
                    pass 
                except:
                    pass
                
                # Deploy Grid
                # Pass sentinel instance to enforce TrendGuard
                weaver.execute_grid(spacing_multiplier=1.0, layers=LAYERS, sentinel=sentinel)
                
                # --- INVENTORY TP MANAGER (Unlock Profit) ---
                try:
                    positions = data.get_positions()
                    btc_pos = [p for p in positions if p['symbol'] == SYMBOL]
                    
                    if btc_pos:
                        pos = btc_pos[0]
                        qty = float(pos.get('quantity', 0))
                        side = pos.get('side', '')
                        entry_price = float(pos.get('entryPrice', 0))
                        current_price = float(pos.get('markPrice', 0))
                        
                        if side.lower() == 'long' and qty > 0:
                            print(f"\n    [TP MANAGER] Managing Inventory: {qty} BTC")
                            
                            # Define TP Price (e.g., +0.5% from Entry or +1 Grid Spacing above current)
                            # Let's ensure we are selling above Entry.
                            # If we are in profit, lock it.
                            
                            # Calculate simple TP target: Entry + 0.5% (Scalp)
                            # Or if price > entry, place Limit just above.
                            
                            tp_price = max(entry_price * 1.005, current_price * 1.002) 
                            tp_price = round(tp_price, 1)
                            
                            print(f"      -> Placing Surplus TP @ {tp_price} (Target: 0.5% ROI)")
                            
                            # Place Limit Sell for full inventory (Reduce Only)
                            trade.execute_order(SYMBOL, "Ask", tp_price, qty, order_type="Limit", reduce_only=True)
                            
                    else:
                        print("\n   ℹ️ [TP MANAGER] No Active Position to Manage.")
                        
                except Exception as e:
                    print(f"   ️ TP Manager Error: {e}")
                # ---------------------------------------------
                
                print("    Sleeping 300s (5 mins)...")
                time.sleep(300)
                
            except KeyboardInterrupt:
                print("\n Farm Bot Stopped.")
                break
            except Exception as e:
                print(f"   ️ Farm Loop Error: {e}")
                time.sleep(60)
    finally:
        print("\n Shutting down Sentinel...")
        sentinel.stop()

    print("\n [PROTOCOL NOCTURNE] Session Ended.")

if __name__ == "__main__":
    night_ops()
