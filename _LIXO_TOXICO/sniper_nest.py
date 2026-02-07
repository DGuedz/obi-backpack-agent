
import os
import time
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# Reuse the logic but in a dedicated loop
from confluence_check import check_triple_confluence
from exponential_sniper import ExponentialSniper

load_dotenv()

def sniper_nest_loop():
    print(" SNIPER NEST: Positioned and Waiting for Target...")
    print("=====================================================")
    print("   Target: IP_USDC_PERP")
    print("   Weapon: $200 (10x Leverage)")
    print("   Strategy: Triple Confluence (Head Shot)")
    
    sniper = ExponentialSniper() # Pre-loaded with $200 logic
    
    while True:
        try:
            # 1. Check Confluence
            # Using the function from confluence_check but we need to capture the return
            # Let's import or reimplement quickly to return the signal string
            # Re-implementing logic here for clean loop control
            
            # --- Confluence Logic Start ---
            # (Simplified for loop speed)
            # Fetch Data
            klines = sniper.data.get_klines(sniper.symbol, interval="5m", limit=50)
            if not klines:
                print("    No data... waiting.")
                time.sleep(10)
                continue
                
            df = pd.DataFrame(klines)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            rsi = sniper.indicators.calculate_rsi(df).iloc[-1]
            bb = sniper.indicators.calculate_bollinger_bands(df)
            price = df['close'].iloc[-1]
            upper = bb['upper'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            
            # Flow
            depth = sniper.data.get_depth(sniper.symbol)
            bids = sum([float(x[1]) for x in depth.get('bids', [])[:10]])
            asks = sum([float(x[1]) for x in depth.get('asks', [])[:10]])
            imbalance = bids / asks if asks > 0 else 1
            
            current_time = time.strftime("%H:%M:%S")
            print(f"\r[{current_time}] ️ Scanning... Price: {price:.4f} | RSI: {rsi:.1f} | Flow: {imbalance:.2f}x", end="", flush=True)
            
            # --- Trigger Logic ---
            signal = None
            
            # LONG HEAD SHOT
            if rsi < 35 and price <= lower and imbalance > 1.5:
                print("\n\n    TARGET ACQUIRED: LONG (Oversold + Support Wall)")
                signal = "Bid"
                
            # SHORT HEAD SHOT
            elif rsi > 65 and price >= upper and imbalance < 0.6: # Sell pressure
                print("\n\n    TARGET ACQUIRED: SHORT (Overbought + Sell Wall)")
                signal = "Ask"
                
            # --- Execution ---
            if signal:
                print("    BOOM! Firing Head Shot...")
                # Execute with Exponential Sniper logic
                notional = sniper.budget * sniper.leverage
                qty = round(notional / price, 1)
                
                res = sniper.trade.execute_order(
                    symbol=sniper.symbol,
                    side=signal,
                    price=None,
                    quantity=str(qty),
                    order_type="Market"
                )
                
                if res and 'id' in res:
                    print(f"    KILL CONFIRMED: {res['id']}")
                    sniper.manage_position(signal, price, qty)
                    break # Mission Accomplished - Exit Loop to avoid churn
                else:
                    print(f"    JAMMED: {res}")
                    time.sleep(5)
            
            time.sleep(5) # Scan every 5s
            
        except KeyboardInterrupt:
            print("\n Sniper Standing Down.")
            break
        except Exception as e:
            print(f"\n️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    sniper_nest_loop()
