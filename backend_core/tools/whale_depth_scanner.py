import sys
import os
import time

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport

def analyze_depth(symbol, transport):
    try:
        # Fetch deep book (100 levels)
        book = transport.get_orderbook_depth(symbol, limit=100)
        if not book:
            return None
            
        bids = book.get('bids', [])
        asks = book.get('asks', [])
        
        # Thresholds for "Whale" orders (Value in USD)
        # We need price to calculate value
        # bid: [price, quantity]
        
        whale_threshold = 5000 # Orders > $5k considered "Significant"
        
        whale_bids_vol = 0
        whale_asks_vol = 0
        retail_bids_vol = 0
        retail_asks_vol = 0
        
        whale_bid_count = 0
        whale_ask_count = 0
        
        # Analyze Bids
        for price_str, qty_str in bids:
            price = float(price_str)
            qty = float(qty_str)
            value = price * qty
            
            if value >= whale_threshold:
                whale_bids_vol += value
                whale_bid_count += 1
            else:
                retail_bids_vol += value
                
        # Analyze Asks
        for price_str, qty_str in asks:
            price = float(price_str)
            qty = float(qty_str)
            value = price * qty
            
            if value >= whale_threshold:
                whale_asks_vol += value
                whale_ask_count += 1
            else:
                retail_asks_vol += value
                
        # Calculate OBIs
        total_whale_vol = whale_bids_vol + whale_asks_vol
        whale_obi = (whale_bids_vol - whale_asks_vol) / total_whale_vol if total_whale_vol > 0 else 0
        
        total_retail_vol = retail_bids_vol + retail_asks_vol
        retail_obi = (retail_bids_vol - retail_asks_vol) / total_retail_vol if total_retail_vol > 0 else 0
        
        return {
            "symbol": symbol,
            "whale_obi": whale_obi,
            "retail_obi": retail_obi,
            "whale_bids": whale_bids_vol,
            "whale_asks": whale_asks_vol,
            "whale_count": whale_bid_count + whale_ask_count
        }
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def main():
    transport = BackpackTransport()
    
    targets = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
        "XRP_USDC_PERP", "APT_USDC_PERP", "NEAR_USDC_PERP"
    ]
    
    print("\nWHALE WATCH: ORDERBOOK DEPTH ANALYSIS")
    print("=" * 80)
    print(f"{'SYMBOL':<15} | {'WHALE OBI':<10} | {'RETAIL OBI':<10} | {'WHALE VOL($)':<15} | {'SIGNAL'}")
    print("-" * 80)
    
    for symbol in targets:
        data = analyze_depth(symbol, transport)
        if data:
            w_obi = data['whale_obi']
            r_obi = data['retail_obi']
            w_vol = data['whale_bids'] + data['whale_asks']
            
            # Signal Logic
            signal = "NEUTRAL"
            if w_obi > 0.2:
                signal = "ACCUMULATION"
            elif w_obi < -0.2:
                signal = "DISTRIBUTION"
            
            # Divergence Check
            if w_obi > 0.2 and r_obi < -0.1:
                signal += " (Retail Panic Selling)"
            elif w_obi < -0.2 and r_obi > 0.1:
                signal += " (Retail Bag Holding)"
                
            print(f"{symbol:<15} | {w_obi:<10.2f} | {r_obi:<10.2f} | ${w_vol:<14.0f} | {signal}")
            time.sleep(0.5)
            
    print("-" * 80)
    print("NOTE: 'Whale OBI' tracks orders > $5k. 'Retail OBI' tracks smaller orders.")

if __name__ == "__main__":
    main()
