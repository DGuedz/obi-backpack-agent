
import os
import sys
import json
import math
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def execute_portfolio():
    transport = BackpackTransport()
    print(" OBI PREDICTION PORTFOLIO EXECUTOR")
    print("   Target: Deploy $5.00 into Arbitrage Opportunities\n")
    
    # 1. Define Targets (Symbol Snippets to Match)
    targets = [
        {
            "name": "Extended > $800M",
            "match_symbol": "FDVEXTD800M",
            "allocation": 2.00,
            "side": "Bid"
        },
        {
            "name": "Paradex > $1.5B",
            "match_symbol": "FDVPARA1N5B",
            "allocation": 1.50,
            "side": "Bid"
        },
        {
            "name": "edgeX > $4B",
            "match_symbol": "FDVEDGEX4B",
            "allocation": 1.50,
            "side": "Bid"
        }
    ]
    
    # 2. Fetch Live Data to Get Exact Symbols and Prices
    print("   Fetching live market data...")
    markets = transport.get_prediction_markets()
    if not markets:
        print("    Error: No markets found.")
        return

    # Flatten markets
    all_outcomes = []
    for m in markets:
        for pm in m.get('predictionMarkets', []):
            all_outcomes.append(pm)
            
    # 3. Match and Execute
    total_deployed = 0.0
    
    for target in targets:
        # Find exact symbol
        match = next((x for x in all_outcomes if target['match_symbol'] in x.get('marketSymbol', '')), None)
        
        if match:
            symbol = match.get('marketSymbol')
            price = float(match.get('activePrice') or 0)
            
            if price <= 0:
                print(f"   ️ Skipping {target['name']}: Price is zero or invalid.")
                continue
                
            # Calculate Quantity
            # Qty = Allocation / Price
            raw_qty = target['allocation'] / price
            qty = math.floor(raw_qty) # Integer contracts usually
            
            if qty < 1:
                print(f"   ️ Skipping {target['name']}: Alloc ${target['allocation']} buys 0 contracts at ${price}.")
                continue
                
            cost = qty * price
            
            print(f"\n    EXECUTING: {target['name']}")
            print(f"      Symbol: {symbol}")
            print(f"      Price: ${price} | Qty: {qty}")
            print(f"      Est. Cost: ${cost:.2f}")
            
            # Execute Order
            # Adding 2% slippage to limit price to ensure fill in beta
            limit_price = round(price * 1.02, 3) 
            
            res = transport.execute_order(
                symbol=symbol,
                order_type="Limit",
                side=target['side'],
                quantity=str(qty),
                price=str(limit_price),
                time_in_force="GTC"
            )
            
            if res and 'id' in res:
                print(f"       ORDER SUCCESS! ID: {res['id']}")
                total_deployed += cost
            else:
                print(f"       ORDER FAILED. Response: {res}")
                
        else:
            print(f"   ️ Could not find market matching: {target['match_symbol']}")
            
    print(f"\n    TOTAL DEPLOYED: ${total_deployed:.2f} / $5.00")

if __name__ == "__main__":
    execute_portfolio()
