
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def analyze_opportunities():
    transport = BackpackTransport()
    print(" OBI STRATEGIC PREDICTION SCANNER")
    print("   Scanning for Logical Arbitrage & Value Bets...\n")
    
    try:
        markets = transport.get_prediction_markets()
        if not markets:
            print("    No active markets.")
            return

        # 1. Group by Series (e.g. "Extended FDV")
        series_groups = {}
        
        for m in markets:
            title_base = m.get('title', '').split('___')[0] # Heuristic grouping
            if title_base not in series_groups:
                series_groups[title_base] = []
            
            # Extract sub-markets
            for pm in m.get('predictionMarkets', []):
                pm['parent_title'] = m.get('title')
                series_groups[title_base].append(pm)

        # 2. Analyze each group for Monotonicity Violations
        # Logic: "FDV > 300M" (Easier) should be MORE expensive than "FDV > 500M" (Harder).
        # If Price(300M) < Price(500M), that's an arbitrage!
        
        for group_name, items in series_groups.items():
            print(f" SERIES: {group_name}")
            
            # Sort items by 'groupLabel' value if possible (e.g. $300M, $500M)
            # Helper to parse "$300M" to integer
            def parse_value(label):
                if not label: return 0
                s = label.replace('$','').replace('M','000000').replace('B','000000000').replace('K','000')
                try:
                    return float(s)
                except:
                    return 0
            
            # Filter only those with groupLabel
            valid_items = [i for i in items if i.get('groupLabel')]
            valid_items.sort(key=lambda x: parse_value(x['groupLabel']))
            
            prev_price = 1.1 # Start high (Probability of > 0 is 100%)
            prev_label = "Zero"
            
            for item in valid_items:
                label = item.get('groupLabel')
                price = float(item.get('activePrice', 0) or 0)
                symbol = item.get('marketSymbol')
                question = item.get('question')
                
                # Check Monotonicity
                # P(Value > X) should decrease as X increases
                # So current price should be <= prev_price
                
                status = " Normal"
                if price > prev_price:
                    status = f" LOGICAL ARBITRAGE! ({price} > {prev_price})"
                    print(f"       OPPORTUNITY: Buy {prev_label} (Cheaper) vs {label} (More Expensive)? Check Logic.")
                    # Actually, if "Greater than 500M" is more expensive than "Greater than 300M",
                    # You should Sell "Greater than 500M" (Overpriced) and Buy "Greater than 300M" (Underpriced).
                    # But since we can only Buy YES usually, we can at least say 500M is Overpriced or 300M is Underpriced.
                
                print(f"   • {label.ljust(8)} | Price: {price:.3f} | {status}")
                
                prev_price = price
                prev_label = label
                
            print("")
            
        # 3. List All "Cheap Long Shots" (Price < 0.10)
        print(" CHEAP LONG SHOTS (Risk < $10 for $100 payout):")
        for m in markets:
            for pm in m.get('predictionMarkets', []):
                price = float(pm.get('activePrice', 0) or 0)
                if 0.01 < price < 0.10:
                    print(f"    {pm.get('groupLabel')} - {pm.get('question')} @ ${price:.3f}")
                    
        # 4. List "Almost Certain" (Price > 0.90) - Free Yield?
        print("\n️ HIGH PROBABILITY (Yield Farming):")
        for m in markets:
            for pm in m.get('predictionMarkets', []):
                price = float(pm.get('activePrice', 0) or 0)
                if price > 0.90:
                    print(f"    {pm.get('groupLabel')} - {pm.get('question')} @ ${price:.3f} (Yield: {(1/price - 1)*100:.2f}%)")

    except Exception as e:
        print(f"    Error: {e}")

if __name__ == "__main__":
    analyze_opportunities()
