
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def whale_detective():
    print("️ WHALE DETECTIVE: Tracking IP Protocol Flows...")
    print("================================================")
    
    # We need to hit Solana RPC or Etherscan (depending on where IP is)
    # IP is likely on Solana (Backpack native) or Ethereum (Story Protocol).
    # IP (Story Protocol) is an L1/L2. But here it's likely the token on a chain.
    # Assuming Solana for Backpack context.
    
    # 1. Fetch recent large transactions (Simulated via Volume/Funding analysis)
    # We can't access raw blockchain RPC here without a node key (Solana/Infura).
    # But we can infer from Funding Rate and CVD (Cumulative Volume Delta) via Backpack API.
    
    # Funding Rate Analysis:
    # If Funding dropped significantly, Baleias sold Spot/Perp to hedge or exited Longs.
    # If Funding spiked, Baleias are longing.
    
    # 2. Check Funding Rate
    url = "https://api.backpack.exchange/api/v1/ticker?symbol=IP_USDC_PERP"
    res = requests.get(url).json()
    
    funding = float(res.get('fundingRate', 0))
    print(f"    Funding Rate: {funding:.6f}")
    
    if funding < 0:
        print("   ️ NEGATIVE FUNDING: Shorts paying Longs. Baleias are HEAVY SHORT.")
        print("   ️ Flow Direction: Money moving into Stablecoins (Cash Out) or hedging Spot bags.")
    else:
        print("    POSITIVE FUNDING: Longs paying Shorts.")
        
    # 3. CVD Inference (Volume Delta)
    # If Price Dropped (-5%) and Volume was Huge -> Aggressive Selling (Market Sell).
    # Where did the money go? 
    # Usually rotated into:
    # A) SOL (Safety/Gas)
    # B) USDC (Cash)
    # C) The next pump (PENGU? FOGO?)
    
    print("\n   ️ Rotation Analysis (Correlation Check):")
    # Check other assets performance in the last 15m
    tickers = requests.get("https://api.backpack.exchange/api/v1/tickers").json()
    
    ip_change = 0
    candidates = []
    
    for t in tickers:
        s = t['symbol']
        c = float(t.get('priceChangePercent', 0))
        if s == "IP_USDC_PERP":
            ip_change = c
        elif "PERP" in s:
            candidates.append((s, c))
            
    print(f"   IP Change (24h): {ip_change:.2f}%")
    
    # Find assets that moved UP while IP moved DOWN (Inverse Correlation)
    print("    Assets Pumping (Potential Rotation Targets):")
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    for s, c in candidates[:5]:
        print(f"      {s}: {c:.2f}%")
        
    print("\n    VERDICT:")
    top_gainer = candidates[0]
    if top_gainer[1] > 5:
        print(f"      Money likely rotated into {top_gainer[0]}.")
    else:
        print("      Money exited to USDC (Risk Off). No obvious rotation pump detected.")

if __name__ == "__main__":
    whale_detective()
