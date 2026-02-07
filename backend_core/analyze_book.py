
import requests
import pandas as pd

def analyze_book():
    symbol = "SOL_USDC_PERP"
    url = f"https://api.backpack.exchange/api/v1/depth?symbol={symbol}"
    
    print(f" ANALYZING BOOK FOR {symbol}")
    
    try:
        resp = requests.get(url)
        data = resp.json()
        
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        # Parse to DataFrame
        df_bids = pd.DataFrame(bids, columns=['price', 'qty'])
        df_asks = pd.DataFrame(asks, columns=['price', 'qty'])
        
        df_bids['price'] = df_bids['price'].astype(float)
        df_bids['qty'] = df_bids['qty'].astype(float)
        
        df_asks['price'] = df_asks['price'].astype(float)
        df_asks['qty'] = df_asks['qty'].astype(float)
        
        # Sort correctly just in case (Bids Descending for analysis, Asks Ascending)
        # Backpack Bids are Ascending (Last is Best). Let's reverse for "Depth from Spread" view.
        df_bids = df_bids.sort_values('price', ascending=False).reset_index(drop=True)
        df_asks = df_asks.sort_values('price', ascending=True).reset_index(drop=True)
        
        best_bid = df_bids.iloc[0]['price']
        best_ask = df_asks.iloc[0]['price']
        
        print(f"Spread: {best_bid} - {best_ask}")
        
        # Analyze immediate depth (Top 20)
        top_20_bids = df_bids.head(20)
        top_20_asks = df_asks.head(20)
        
        avg_bid_qty = top_20_bids['qty'].mean()
        avg_ask_qty = top_20_asks['qty'].mean()
        
        print(f"\nTop 20 Bids Avg Qty: {avg_bid_qty:.2f}")
        print(f"Top 20 Asks Avg Qty: {avg_ask_qty:.2f}")
        
        # Detect Walls (Orders > 3x Avg)
        bid_walls = top_20_bids[top_20_bids['qty'] > avg_bid_qty * 3]
        ask_walls = top_20_asks[top_20_asks['qty'] > avg_ask_qty * 3]
        
        print("\n BID WALLS (Support):")
        if not bid_walls.empty:
            print(bid_walls)
        else:
            print("None detected.")
            
        print("\n ASK WALLS (Resistance):")
        if not ask_walls.empty:
            print(ask_walls)
        else:
            print("None detected.")
            
        # Cumulative Volume
        cum_bid = top_20_bids['qty'].sum()
        cum_ask = top_20_asks['qty'].sum()
        
        print(f"\nPressure (Top 20):")
        print(f"Bids Total: {cum_bid:.2f}")
        print(f"Asks Total: {cum_ask:.2f}")
        print(f"Ratio: {cum_bid/cum_ask:.2f} ( >1 Bullish, <1 Bearish)")

    except Exception as e:
        print(e)

if __name__ == "__main__":
    analyze_book()
