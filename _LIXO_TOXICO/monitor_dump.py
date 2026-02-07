
import os
import time
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

def monitor_dump():
    symbol = "IP_USDC_PERP"
    print(f" MONITORING DUMP: {symbol}")
    print("=" * 40)
    
    # 1. Check Price Action
    try:
        klines = data.get_klines(symbol, interval="1m", limit=5)
        if not klines:
            print(" No data.")
            return

        print("Recent 5m Candles:")
        for k in klines:
            # open, high, low, close, volume
            o = float(k['open'])
            c = float(k['close'])
            v = float(k['volume'])
            pct = (c - o) / o * 100
            color = "" if pct < 0 else "🟢"
            print(f"   {color} {c:.4f} ({pct:.2f}%) | Vol: {v:.1f}")
            
        current_price = float(klines[-1]['close'])
        
        # 2. Check Order Book for Support
        depth = data.get_depth(symbol)
        if depth:
            bids = depth.get('bids', [])[:5]
            asks = depth.get('asks', [])[:5]
            
            print("\nOrder Book Top 5:")
            print("   ASKS (Resistance) | BIDS (Support)")
            for i in range(5):
                a_p = asks[i][0] if i < len(asks) else "-"
                a_v = asks[i][1] if i < len(asks) else "-"
                b_p = bids[i][0] if i < len(bids) else "-"
                b_v = bids[i][1] if i < len(bids) else "-"
                print(f"   {a_p} ({a_v}) | {b_p} ({b_v})")
                
            # Wall detection
            total_bids = sum([float(x[1]) for x in depth.get('bids', [])])
            total_asks = sum([float(x[1]) for x in depth.get('asks', [])])
            
            print(f"\n   Total Bids (Support): {total_bids:.1f}")
            print(f"   Total Asks (Pressure): {total_asks:.1f}")
            
            if total_asks > total_bids * 1.5:
                print("    HEAVY SELL PRESSURE DETECTED (Dump Active)")
            else:
                print("   ️ Balanced / Fighting Support")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitor_dump()
