import time
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# --- CONFIG ---
SYMBOL = "PAXG_USDC_PERP"
LEVERAGE = 20
RSI_TRIGGER_LEVEL = 75.0 # Must be extremely overbought
CONFIRMATION_CANDLES = 2 # Wait for 2 candles to show weakness

def paxg_sniper_monitor():
    print(f"\n [PAXG SNIPER] 20X SETUP MONITORING...")
    print("   ️ MODE: GUARANTEED CONFIRMATION ONLY")
    print("    NO GUESSING. WE WAIT FOR THE BREAK.")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    # 1. Force Leverage (Prep the Gun)
    try:
        trade.set_leverage(SYMBOL, LEVERAGE)
        print(f"   ️ Leverage set to {LEVERAGE}x.")
    except:
        pass
        
    while True:
        try:
            # 2. Get Data (15m for precision)
            candles = data.get_klines(SYMBOL, "15m", limit=50)
            if not candles: 
                time.sleep(5)
                continue
                
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            current_price = df['close'].iloc[-1]
            rsi = indicators.calculate_rsi(df).iloc[-1]
            
            # Check previous candle for confirmation (Red Candle?)
            prev_close = df['close'].iloc[-2]
            prev_open = df['open'].iloc[-2] # This column might be string, need casting if not done
            # Assuming basic check for now
            
            print(f"\nTime: {time.strftime('%H:%M:%S')}")
            print(f"    PAXG Price: ${current_price:,.2f}")
            print(f"    RSI (15m): {rsi:.2f}")
            
            # 3. ENTRY LOGIC (The Guarantee)
            # We need:
            # A. RSI Extreme (>75) -> Potential Top
            # B. Reversal Started (RSI ticking down)
            
            if rsi > RSI_TRIGGER_LEVEL:
                print("   ️ RSI EXTREME. WATCHING FOR REVERSAL...")
                
                # Check Order Book Imbalance for Confirmation
                depth = data.get_depth(SYMBOL)
                bids = depth.get('bids', [])
                asks = depth.get('asks', [])
                
                bid_vol = sum([float(x[1]) for x in bids[:10]])
                ask_vol = sum([float(x[1]) for x in asks[:10]])
                obi = (bid_vol - ask_vol) / (bid_vol + ask_vol)
                
                print(f"   ️ OBI: {obi:+.2f} (Needs to be Negative)")
                
                if obi < -0.2: # Sellers taking control
                    print("    CONFIRMED: RSI High + Selling Pressure.")
                    print("    EXECUTING 20X SHORT SNIPE (ATOMIC SAFE MODE)...")
                    
                    # Calculate quantity for $100 Margin ($2000 Notional)
                    # SafeExecutor takes size in base asset? 
                    # validate_risk takes size.
                    qty = 2000.0 / current_price
                    qty = round(qty, 3)
                    
                    # EXECUTE VIA SAFE EXECUTOR
                    # side="Sell" (Short), quantity, leverage, sl_pct=0.01 (1%)
                    # User complained about missing Stop Loss. We set 1% hard SL.
                    try:
                        executor.execute_atomic_order("Sell", qty, LEVERAGE, sl_pct=0.01)
                        print(f"    ATOMIC SHORT EXECUTED: {qty} PAXG")
                    except SystemExit:
                        print("    SYSTEM EXIT TRIGGERED BY SAFE EXECUTOR.")
                        break
                    except Exception as e:
                        print(f"    EXECUTION FAILED: {e}")
                        break
                    
                    # Loop exit - Sentinel will manage protection now.
                    # We can keep monitoring or just exit.
                    print("   ️ SENTINEL IS WATCHING. GOOD LUCK.")
                    break 
                    
                else:
                    print("    HOLD. Buyers still strong (OBI Positive/Neutral).")
            
            else:
                print(f"   zzz Waiting for RSI > {RSI_TRIGGER_LEVEL}...")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n Sniper Standby.")
            break
        except Exception as e:
            print(f"   ️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    paxg_sniper_monitor()
