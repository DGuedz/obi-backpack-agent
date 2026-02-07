import os
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"

def analyze_onchain_proxy():
    print(f"\n [ON-CHAIN PROXY ORACLE] DECODING WHALE INTENT FOR {SYMBOL}...")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    try:
        # 1. FETCH ORDER BOOK (LIQUIDITY MAP)
        depth = data.get_depth(SYMBOL)
        if not depth:
            print("    Failed to fetch Order Book.")
            return

        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # 2. ANALYZE WALLS (SMART MONEY POSITIONING)
        # We look at the top 50 levels to see where the heavy capital is sitting.
        
        bid_vol = 0.0
        ask_vol = 0.0
        weighted_bid_price = 0.0
        weighted_ask_price = 0.0
        
        # Analyze Bids (Support)
        for price, qty in bids[:50]:
            p = float(price)
            q = float(qty)
            bid_vol += q
            weighted_bid_price += (p * q)
            
        avg_bid_price = weighted_bid_price / bid_vol if bid_vol > 0 else 0
            
        # Analyze Asks (Resistance)
        for price, qty in asks[:50]:
            p = float(price)
            q = float(qty)
            ask_vol += q
            weighted_ask_price += (p * q)
            
        avg_ask_price = weighted_ask_price / ask_vol if ask_vol > 0 else 0
            
        # 3. OBI (ORDER BOOK IMBALANCE)
        # OBI > 0: Buying Pressure
        # OBI < 0: Selling Pressure
        total_vol = bid_vol + ask_vol
        obi = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0
        
        print("\n LIQUIDITY STRUCTURE (WHALE MAP):")
        print(f"   ️ BID WALL (Buyers):  {bid_vol:.4f} BTC (Avg: ${avg_bid_price:,.2f})")
        print(f"   ️ ASK WALL (Sellers): {ask_vol:.4f} BTC (Avg: ${avg_ask_price:,.2f})")
        print(f"   ️ IMBALANCE (OBI):    {obi:+.4f}")
        
        # 4. FUNDING RATE (CROWD SENTIMENT)
        # Positive Funding: Longs paying Shorts (Crowd is Bullish -> Contrarian Bearish?)
        # Negative Funding: Shorts paying Longs (Crowd is Bearish -> Contrarian Bullish?)
        
        tickers = data.get_tickers()
        btc_ticker = next((t for t in tickers if t['symbol'] == SYMBOL), None)
        mark_price = float(btc_ticker.get('markPrice', 0)) if btc_ticker else 0
        
        # Backpack API usually provides funding in ticker or separate endpoint.
        # Assuming we infer sentiment from price vs walls if funding not explicit here.
        # But let's use the OBI verdict.
        
        print("\n ORACLE VERDICT:")
        
        if obi > 0.15:
            direction = "BULLISH (UP)"
            confidence = "HIGH" if obi > 0.3 else "MODERATE"
            action = "Support is building. Whales are catching the knife."
        elif obi < -0.15:
            direction = "BEARISH (DOWN)"
            confidence = "HIGH" if obi < -0.3 else "MODERATE"
            action = "Resistance is heavy. Whales are capping the upside."
        else:
            direction = "NEUTRAL (CHOP)"
            confidence = "LOW"
            action = "Equilibrium. Wait for a wall to break."
            
        print(f"    DIRECTION: {direction}")
        print(f"    CONFIDENCE: {confidence}")
        print(f"    INSIGHT: {action}")
        
        print(f"\n    CURRENT PRICE: ${mark_price:,.2f}")
        
        # 5. STRATEGIC RECOMMENDATION
        if direction.startswith("BULLISH"):
             print("    RECOMMENDATION: HOLD/BUY. The dip is being bought.")
        elif direction.startswith("BEARISH"):
             print("   ️ RECOMMENDATION: HEDGE/SELL. Upside is limited.")
        else:
             print("   ⏸️ RECOMMENDATION: WAIT. No clear signal.")

    except Exception as e:
        print(f"    Oracle Error: {e}")

if __name__ == "__main__":
    analyze_onchain_proxy()
