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
SYMBOL = "BTC_USDC_PERP"
EXIT_TARGET = 92000.0
EMA_200_THRESHOLD = 92209.0 # Dynamic? Better to calc.

def monitor_recovery():
    print("\n [RECOVERY MONITOR] WATCHING VITAL SIGNS...")
    print(f"    Exit Target: ${EXIT_TARGET:,.2f}")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    while True:
        try:
            # 1. Get Live Data
            candles = data.get_klines(SYMBOL, "1h", limit=200)
            if not candles: 
                time.sleep(5)
                continue
                
            df = pd.DataFrame(candles)
            df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
            df['close'] = df['close'].astype(float)
            
            current_price = df['close'].iloc[-1]
            ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
            rsi = indicators.calculate_rsi(df).iloc[-1]
            
            # 2. Status Report
            dist_to_exit = EXIT_TARGET - current_price
            trend_status = "BEARISH (Trap)" if current_price < ema_200 else "BULLISH (Recovered)"
            
            print(f"\nTime: {time.strftime('%H:%M:%S')}")
            print(f"    Price: ${current_price:,.2f}")
            print(f"    EMA 200: ${ema_200:,.2f} ({trend_status})")
            print(f"    RSI (1h): {rsi:.2f}")
            
            # 3. Decision Logic
            
            # SCENARIO A: Miracle Recovery (Price > EMA 200)
            if current_price > ema_200:
                print("    TREND RECOVERED! Cancelling Emergency Exit to let it run.")
                trade.cancel_all_orders(SYMBOL)
                print("    Mode switched to: HOLD FOR PROFIT.")
                break # End emergency monitor
                
            # SCENARIO B: Exit Target Hit (Check if filled)
            # (API would fill it, we just watch)
            if current_price >= EXIT_TARGET:
                print("    EXIT TARGET REACHED. Checking fill...")
                # We could check position here. If 0, we are out.
                positions = data.get_positions()
                btc_pos = [p for p in positions if p['symbol'] == SYMBOL]
                if not btc_pos or float(btc_pos[0].get('quantity', 0)) == 0:
                    print("    POSITION CLOSED. CAPITAL SAVED.")
                    break
            
            # SCENARIO C: Stalling (RSI > 60 but Price < 91.5k)
            # If we get overbought on 1h but fail to break resistance, we might need to lower exit.
            if rsi > 60 and current_price < 91500:
                print("   ️ WARNING: Momentum fading (High RSI, Low Price). Consider lowering Exit.")
            
            print(f"   ⏳ Distance to Exit: ${dist_to_exit:.2f}")
            
            time.sleep(10) # Fast updates
            
        except KeyboardInterrupt:
            print("\n Monitor Stopped.")
            break
        except Exception as e:
            print(f"   ️ Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_recovery()
