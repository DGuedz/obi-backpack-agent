import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

# --- CONFIG ---
GOAL_VOLUME = 1_000_000.00

def check_volume():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print(f"\n VOLUME TRACKER: 7-DAY AUDIT")
    print(f"==================================================")
    
    # Fetch fill history (Max 1000 to cover 7 days if possible, or paginate)
    # Backpack API limit is usually 100 per call, need pagination for accurate 7d
    # But for quick check, let's pull max allowed and filter
    
    print("    Fetching fill history from API (Paginated)...")
    try:
        total_volume_7d = 0.0
        today_volume = 0.0
        count = 0
        
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        offset = 0
        limit = 1000
        keep_fetching = True
        
        while keep_fetching:
            print(f"      Fetching batch offset={offset}...")
            fills = data.get_fill_history(limit=limit, offset=offset)
            
            if not fills:
                break
                
            for fill in fills:
                # Parse timestamp
                ts_val = fill.get('timestamp')
                try:
                    if isinstance(ts_val, str):
                        ts = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                        ts = ts.replace(tzinfo=None)
                    else:
                        ts = datetime.fromtimestamp(int(ts_val) / 1000.0)
                except:
                    continue
                
                if ts < seven_days_ago:
                    keep_fetching = False
                    # Stop processing this batch as we went back enough
                    # Assuming API returns newest first (descending)
                    break
                    
                price = float(fill.get('price', 0))
                qty = float(fill.get('quantity', 0))
                notional = price * qty
                
                total_volume_7d += notional
                count += 1
                
                if ts >= start_of_today:
                    today_volume += notional
            
            # Prepare next batch
            if keep_fetching:
                if len(fills) < limit:
                    keep_fetching = False
                else:
                    offset += limit
                    time.sleep(0.2) # Rate limit friendly
                
        progress_pct = (total_volume_7d / GOAL_VOLUME) * 100
        remaining = GOAL_VOLUME - total_volume_7d
        
        print(f" LAST 7 DAYS VOLUME:  ${total_volume_7d:,.2f}")
        print(f"️ TODAY'S VOLUME:      ${today_volume:,.2f}")
        print(f" TRADES COUNTED:      {count}")
        print(f"--------------------------------------------------")
        print(f" SEASON GOAL:         ${GOAL_VOLUME:,.2f}")
        print(f" PROGRESS:            {progress_pct:.2f}%")
        
        if remaining > 0:
            print(f"⏳ REMAINING:           ${remaining:,.2f}")
            avg_trade_size = 1000.0 # Aegis Standard
            trades_needed = remaining / avg_trade_size
            print(f" TRADES TO GO:        ~{int(trades_needed)} (at $1000/trade)")
        else:
            print(f" GOAL ACHIEVED!       +${abs(remaining):,.2f} Surplus")
            
        print(f"==================================================")
        
    except Exception as e:
        print(f"    Error calculating volume: {e}")

if __name__ == "__main__":
    check_volume()
