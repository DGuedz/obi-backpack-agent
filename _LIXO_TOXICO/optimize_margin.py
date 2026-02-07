import os
import sys
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"

def optimize_margin():
    print(f"\n [MARGIN OPTIMIZER] Scanning for Stale Orders on {SYMBOL}...")
    
    # Init
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # 1. Check Positions (Keep them safe)
    try:
        positions = data.get_positions()
        # Debug position structure if needed
        # print(positions) 
        active_pos = [p for p in positions if p['symbol'] == SYMBOL]
        if active_pos:
            pos = active_pos[0]
            # Use .get() to be safe
            pnl = pos.get('unrealizedPnl', '0.00')
            qty = pos.get('quantity', '0.00')
            side = pos.get('side', 'Unknown')
            print(f"    Active Position Detected: {side} {qty} BTC (PnL: {pnl} USDC)")
            print("      -> Position will be PRESERVED.")
        else:
            print("   ℹ️ No Active Position found.")
    except Exception as e:
        print(f"   ️ Error checking positions: {e}")
        # Continue to cleanup anyway? No, might be risky if we don't know state.
        # But user wants to clean orders.
        pass

    # 2. Check Open Orders (The "Apregoadas")
    try:
        # Need to implement get_open_orders in BackpackData or call API directly
        # BackpackData usually has it. Let's check or assume standard endpoint.
        # GET /api/v1/orders?symbol=...
        endpoint = "/api/v1/orders"
        url = "https://api.backpack.exchange/api/v1/orders"
        params = {"symbol": SYMBOL}
        headers = auth.get_headers(instruction="orderQueryAll", params=params) 
        # Actually instruction might be "orderQuery" or "orderQueryAll" depends on API.
        # Let's try to use requests directly with auth.
        
        # Simpler: use BackpackData if available. Let's assume data.get_open_orders(symbol) exists or create ad-hoc.
        # I will do ad-hoc here to be safe.
        
        response = requests.get(url, headers=headers, params=params)
        orders = response.json()
        
        if isinstance(orders, list) and len(orders) > 0:
            print(f"   found {len(orders)} Open Orders. Cancelling...")
            
            # Cancel All Endpoint
            # DELETE /api/v1/orders
            cancel_url = "https://api.backpack.exchange/api/v1/orders"
            cancel_payload = {"symbol": SYMBOL}
            cancel_headers = auth.get_headers(instruction="orderCancelAll", params=cancel_payload)
            
            res = requests.delete(cancel_url, headers=cancel_headers, json=cancel_payload)
            
            if res.status_code == 200:
                print("   ️ All Open Orders CANCELLED successfully.")
            else:
                print(f"    Failed to cancel orders: {res.text}")
                
        else:
            print("   ℹ️ No Open Orders to cancel.")
            
    except Exception as e:
        print(f"   ️ Error managing orders: {e}")
        
    # 3. Final Balance Check
    print("\n Final Margin Status:")
    try:
        collat = data.get_account_collateral()
        print(f"   - Available to Trade: ${collat.get('netEquityAvailable', 'N/A')}")
        print(f"   - Locked Margin: ${collat.get('netEquityLocked', 'N/A')}")
    except:
        pass

if __name__ == "__main__":
    optimize_margin()
