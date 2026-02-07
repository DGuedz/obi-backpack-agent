import os
import sys
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# Mock colored for compatibility
def colored(text, color=None, attrs=None):
    return text

load_dotenv()

def main():
    print(colored(" BTC SURF MONITOR: AUTO-BREAKEVEN ACTIVATED", "cyan", attrs=['bold']))
    print("-" * 60)

    api_key = os.getenv("BACKPACK_API_KEY")
    api_secret = os.getenv("BACKPACK_API_SECRET")
    auth = BackpackAuth(api_key, api_secret)
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    symbol = "BTC_USDC_PERP"
    
    # 1. Get Position Details
    positions = data.get_positions()
    pos = next((p for p in positions if p['symbol'] == symbol and float(p.get('netQuantity', 0)) != 0), None)
    
    if not pos:
        print(" No active BTC position found.")
        return
        
    entry_price = float(pos['entryPrice'])
    quantity = float(pos.get('netQuantity', 0))
    side = "Long" if quantity > 0 else "Short"
    
    if side != "Long":
        print("️ Only LONG positions supported for this logic.")
        return

    # 2. Define Parameters
    # Trigger: When to move SL? Let's say +0.4% move (covers fees + confirms momentum)
    trigger_offset = entry_price * 0.004 
    trigger_price = entry_price + trigger_offset
    
    # New SL: Entry + small buffer for fees
    new_sl_price = entry_price + 50 
    
    print(f" Entry Price:    ${entry_price:.2f}")
    print(f" Surf Trigger:   ${trigger_price:.2f} (When price hits this...)")
    print(f"️ New Stop Loss:  ${new_sl_price:.2f} (...we move SL here)")
    print(f" Final Target:   $99,500.00")
    print("-" * 60)
    print("⏳ Monitoring price... (Press Ctrl+C to stop)")
    
    sl_moved = False
    
    while not sl_moved:
        try:
            # Check Price
            ticker = data.get_ticker(symbol)
            current_price = float(ticker.get('lastPrice', 0))
            
            # Print Status
            dist_to_trigger = trigger_price - current_price
            status_color = "green" if dist_to_trigger <= 0 else "yellow"
            
            sys.stdout.write(f"\rCurrent: ${current_price:.2f} | Dist to Trigger: ${dist_to_trigger:.2f}   ")
            sys.stdout.flush()
            
            if current_price >= trigger_price:
                print(f"\n\n TRIGGER HIT! Moving Stop Loss to Breakeven...")
                
                # 1. Cancel Existing Open Orders (Old SL/TP)
                # NOTE: We want to keep TP at 99,500. 
                # Better to just cancel the STOP MARKET order specifically if possible.
                # But API 'cancel_open_orders' usually nukes all.
                # Let's verify open orders first.
                
                orders = data.get_open_orders()
                # Find the Stop Loss order
                for o in orders:
                    if o['symbol'] == symbol and o['side'] == 'Ask' and o['orderType'] == 'Market': 
                         # Trigger Market usually shows as Market with triggerPrice
                         # Or verify logic. Backpack might verify differently.
                         # Safest: Cancel ALL for symbol and re-place TP.
                         pass
                
                print("   • Cancelling old protection...")
                trade.cancel_open_orders(symbol)
                time.sleep(1)
                
                # 2. Place New SL @ Breakeven
                print(f"   • Setting New SL @ ${new_sl_price:.2f}...")
                trade.execute_order(
                    symbol=symbol,
                    side="Ask",
                    price="0",
                    order_type="Market",
                    quantity=str(abs(quantity)),
                    trigger_price=str(new_sl_price)
                )
                
                # 3. Re-place TP @ $99,500
                print(f"   • Restoring TP @ $99,500...")
                trade.execute_order(
                    symbol=symbol,
                    side="Ask",
                    price="99500",
                    order_type="Limit",
                    quantity=str(abs(quantity))
                )
                
                print(f"\n SURF MODE ACTIVATED! Position is Risk Free.")
                sl_moved = True
                break
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n Monitor stopped by user.")
            break
        except Exception as e:
            print(f"\n Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
