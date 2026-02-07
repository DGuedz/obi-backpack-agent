import os
import time
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

def investigate_drop():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print(f"\n️‍️ VOLUME DROP INVESTIGATION (10-DAY ANALYSIS)")
    print(f"==================================================")
    
    # 1. Fetch deep history (10 days)
    print("    Pulling deep history (10 days)...")
    
    now = datetime.now()
    ten_days_ago = now - timedelta(days=10)
    
    all_fills = []
    offset = 0
    limit = 1000
    keep_fetching = True
    
    while keep_fetching:
        try:
            fills = data.get_fill_history(limit=limit, offset=offset)
            if not fills: break
            
            batch_count = 0
            for fill in fills:
                # Parse timestamp
                ts_val = fill.get('timestamp')
                try:
                    if isinstance(ts_val, str):
                        ts = datetime.fromisoformat(ts_val.replace('Z', '+00:00')).replace(tzinfo=None)
                    else:
                        ts = datetime.fromtimestamp(int(ts_val) / 1000.0)
                except:
                    continue
                
                if ts < ten_days_ago:
                    keep_fetching = False
                    break
                
                all_fills.append({
                    'timestamp': ts,
                    'price': float(fill.get('price', 0)),
                    'quantity': float(fill.get('quantity', 0)),
                    'symbol': fill.get('symbol'),
                    'side': fill.get('side')
                })
                batch_count += 1
            
            if len(fills) < limit: keep_fetching = False
            else: offset += limit
            
            # print(f"      Pulled {len(all_fills)} fills so far...")
            time.sleep(0.1)
            
        except Exception as e:
            print(f"   ️ Error fetching: {e}")
            break
            
    # 2. Group by Day
    df = pd.DataFrame(all_fills)
    if df.empty:
        print("    No data found.")
        return

    df['notional'] = df['price'] * df['quantity']
    df['date'] = df['timestamp'].dt.date
    
    daily_vol = df.groupby('date')['notional'].sum().sort_index(ascending=False)
    
    # 3. Analyze the Rolling Window Effect
    today = now.date()
    seven_days_ago_date = (now - timedelta(days=7)).date()
    eight_days_ago_date = (now - timedelta(days=8)).date()
    
    print("\n DAILY VOLUME BREAKDOWN:")
    print(f"{'DATE':<12} | {'VOLUME':<15} | {'STATUS'}")
    print("-" * 45)
    
    rolling_7d_sum = 0
    dropped_sum = 0
    
    for date, vol in daily_vol.items():
        status = ""
        if date > seven_days_ago_date:
            status = " IN (Active)"
            rolling_7d_sum += vol
        elif date == seven_days_ago_date:
            status = "️ DROPPING SOON"
            rolling_7d_sum += vol
        elif date == eight_days_ago_date:
            status = " OUT (Dropped)"
            dropped_sum += vol
        else:
            status = " OUT"
            
        print(f"{str(date):<12} | ${vol:,.2f}    | {status}")
        
    print("-" * 45)
    print(f" CURRENT 7D CALC: ${rolling_7d_sum:,.2f}")
    if dropped_sum > 1000:
        print(f" VOLUME LOST (Day T-8): -${dropped_sum:,.2f}")
        print(f"   -> This explains the drop. A big day fell out of the window.")
    else:
        print(f"   -> Drop might be due to lower activity today vs T-7.")

if __name__ == "__main__":
    investigate_drop()
