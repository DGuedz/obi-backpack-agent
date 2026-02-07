
import os
import sys
import math
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def deploy_prediction_heavy():
    transport = BackpackTransport()
    print(" OBI PREDICTION HEAVY DEPLOYMENT")
    print("   Strategy: 50% Allocation on Best Arbitrage Opportunities\n")
    
    # 1. Check Capital
    # Since balance query might fail or return locked collateral, 
    # we'll assume available from previous context or try to fetch.
    # For safety, we will fetch 'USDC' available.
    
    try:
        collateral = transport.get_account_collateral()
        usdc_avail = 0.0
        if collateral and 'USDC' in collateral:
            usdc_avail = float(collateral['USDC'].get('available', 0))
        
        print(f" AVAILABLE USDC: ${usdc_avail:.2f}")
        
        # If balance is low (e.g. < $1), it might be locked in orders.
        # Check Open Orders value
        orders = transport.get_open_orders()
        locked_in_orders = 0.0
        if orders:
            for o in orders:
                if 'PREDICTION' in o['symbol']:
                    locked_in_orders += float(o['price']) * float(o['quantity'])
        
        print(f" LOCKED IN PREDICTION ORDERS: ${locked_in_orders:.2f}")
        
        total_prediction_capital = usdc_avail + locked_in_orders
        target_allocation = total_prediction_capital * 0.50 # 50% of total capacity? 
        # Or user said "50% da margem restante". Let's use 50% of AVAILABLE.
        
        deploy_amount = usdc_avail * 0.50
        print(f" DEPLOYING: ${deploy_amount:.2f} (50% of Available)")
        
        if deploy_amount < 1.0:
            print(" Insufficient funds to deploy heavy.")
            return

    except Exception as e:
        print(f" Error checking balance: {e}")
        return

    # 2. Targets (The Arbitrage List)
    # Priority: Paradex > 1.5B (High Reward) and edgeX > 4B (Arbitrage)
    targets = [
        {
            "symbol": "FDVPARA1N5B_USDC_PREDICTION",
            "name": "Paradex > 1.5B",
            "weight": 0.40 # 40% of deploy amount
        },
        {
            "symbol": "FDVEDGEX4B_USDC_PREDICTION",
            "name": "edgeX > 4B",
            "weight": 0.30
        },
        {
            "symbol": "FDVEXTD800M_USDC_PREDICTION",
            "name": "Extended > 800M",
            "weight": 0.30
        }
    ]
    
    # 3. Execution Loop
    print("\n EXECUTING ALLOCATION...")
    
    # Get fresh prices
    markets = transport.get_prediction_markets()
    market_map = {}
    if markets:
        for m in markets:
            for pm in m.get('predictionMarkets', []):
                market_map[pm.get('marketSymbol')] = float(pm.get('activePrice') or 0)
    
    for t in targets:
        symbol = t['symbol']
        alloc = deploy_amount * t['weight']
        price = market_map.get(symbol, 0.0)
        
        if price <= 0:
            print(f"   ️ Skipping {t['name']}: Invalid Price")
            continue
            
        # Quantity
        qty = math.floor(alloc / price)
        if qty < 1: continue
        
        cost = qty * price
        
        print(f"    {t['name']}: Buying {qty}x @ ${price:.3f} (Est: ${cost:.2f})")
        
        # Execute Limit Order (PostOnly if possible, but standard Limit for fill)
        # Adding slippage 2%
        limit_price = round(price * 1.02, 3)
        
        res = transport.execute_order(
            symbol=symbol,
            order_type="Limit",
            side="Bid",
            quantity=str(qty),
            price=str(limit_price),
            time_in_force="GTC"
        )
        
        if res and 'id' in res:
            print(f"       ORDER SENT: {res['id']}")
        else:
            print(f"       FAILED: {res}")

if __name__ == "__main__":
    deploy_prediction_heavy()
