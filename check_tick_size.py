import requests
import json

def check_markets():
    try:
        response = requests.get("https://api.backpack.exchange/api/v1/markets")
        markets = response.json()
        
        targets = ["SKR_USDC_PERP", "FOGO_USDC_PERP", "BTC_USDC_PERP"]
        
        print(f"{'SYMBOL':<20} | {'TICK SIZE':<10} | {'STEP SIZE':<10} | {'MIN QTY':<10}")
        print("-" * 60)
        
        for m in markets:
            if m['symbol'] in targets:
                filters = m.get('filters', {})
                price_filters = filters.get('price', {})
                qty_filters = filters.get('quantity', {})
                
                tick_size = price_filters.get('tickSize', 'N/A')
                step_size = qty_filters.get('stepSize', 'N/A')
                min_qty = qty_filters.get('minQuantity', 'N/A')
                
                print(f"{m['symbol']:<20} | {tick_size:<10} | {step_size:<10} | {min_qty:<10}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_markets()
