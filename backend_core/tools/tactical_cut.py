import sys
import os
import time

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport

def main():
    transport = BackpackTransport()
    
    # Targets to CUT
    targets = ["LINK_USDC_PERP", "WIF_USDC_PERP"]
    
    print("️ TACTICAL CUT EXECUTION INITIATED")
    print(f"   Targets: {targets}")
    print("=" * 60)
    
    try:
        positions = transport.get_positions()
    except AttributeError:
        positions = transport.get_open_positions() if hasattr(transport, 'get_open_positions') else []

    if not positions:
        print(" No positions found to cut.")
        return

    for p in positions:
        symbol = p.get('symbol')
        if symbol in targets:
            print(f"\n FOUND TARGET: {symbol}")
            
            # Determine Size and Side
            raw_qty = p.get('quantity')
            if raw_qty is None: raw_qty = p.get('netQuantity', 0)
            qty = float(raw_qty)
            
            if qty == 0:
                print("   ️ Quantity is 0, skipping.")
                continue
                
            current_side = "Long" if qty > 0 else "Short"
            close_side = "Ask" if current_side == "Long" else "Bid" # API uses Bid/Ask for orders
            
            abs_qty = abs(qty)
            
            print(f"   Current: {current_side} | Size: {abs_qty}")
            print(f"   -> EXECUTING CLOSE ORDER ({close_side})...")
            
            # Execute Market Order to Close
            try:
                order = transport.execute_order(
                    symbol=symbol,
                    side=close_side,
                    order_type="Market",
                    quantity=str(abs_qty)
                )
                
                if order and (order.get('id') or order.get('orderId')):
                    print(f"    SUCCESS: Position Closed. ID: {order.get('id') or order.get('orderId')}")
                else:
                    print(f"    FAILED: API did not return Order ID. Response: {order}")
                    
            except Exception as e:
                print(f"    EXCEPTION during execution: {e}")
                
    print("\n TACTICAL CUT COMPLETE.")

if __name__ == "__main__":
    main()
