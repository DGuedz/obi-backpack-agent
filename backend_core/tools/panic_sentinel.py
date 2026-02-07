
import os
import sys
import time
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def panic_sentinel():
    transport = BackpackTransport()
    symbol = "BTC_USDC_PERP"
    
    # PARAMETROS DE EMERGENCIA
    HARD_STOP_PRICE = 76500.0 # Se bater aqui, vende a mercado.
    TARGET_EXIT_PRICE = 77000.0 # Se subir um pouco, sai para reduzir prejuízo.
    
    print(f" OBI PANIC SENTINEL ACTIVATED ({symbol})")
    print(f"    HARD STOP: ${HARD_STOP_PRICE}")
    print(f"    ESCAPE TARGET: ${TARGET_EXIT_PRICE}")
    print("    MONITORING PRICE ACTION (High Frequency)...")
    
    while True:
        try:
            # Get Ticker (Faster than depth)
            ticker = transport.get_ticker(symbol)
            if not ticker:
                time.sleep(1)
                continue
                
            last_price = float(ticker.get('lastPrice', 0))
            print(f"   Price: ${last_price:.2f} ...", end='\r')
            
            # 1. CHECK HARD STOP
            if last_price <= HARD_STOP_PRICE:
                print(f"\n\n CRITICAL: PRICE BROKE ${HARD_STOP_PRICE}!")
                print("   ️ EXECUTING EMERGENCY MARKET SELL...")
                
                # Get position size first to close exactly
                pos = transport.get_positions()
                size = 0
                side = ""
                for p in pos:
                    if p['symbol'] == symbol:
                        size = p['quantity']
                        side = p['side'] # Long or Short
                        break
                
                if size and float(size) > 0:
                    exit_side = "Ask" if side == "Long" else "Bid"
                    res = transport.execute_order(symbol, "Market", exit_side, size)
                    print(f"    POSITION CLOSED: {res}")
                    break
                else:
                    print("   ️ No open position found to close.")
                    break
            
            # 2. CHECK ESCAPE TARGET
            if last_price >= TARGET_EXIT_PRICE:
                print(f"\n\n ESCAPE OPPORTUNITY: PRICE HIT ${TARGET_EXIT_PRICE}!")
                print("   ️ EXECUTING EXIT TO REDUCE LOSS...")
                
                # Close Logic (Same as above)
                pos = transport.get_positions()
                size = 0
                side = ""
                for p in pos:
                    if p['symbol'] == symbol:
                        size = p['quantity']
                        side = p['side']
                        break
                
                if size and float(size) > 0:
                    exit_side = "Ask" if side == "Long" else "Bid"
                    res = transport.execute_order(symbol, "Market", exit_side, size)
                    print(f"    POSITION CLOSED (ESCAPE): {res}")
                    break
                else:
                    print("   ️ No open position found to close.")
                    break

            time.sleep(1) # 1s poll
            
        except KeyboardInterrupt:
            print("\n    Sentinel Stopped by User.")
            break
        except Exception as e:
            print(f"   ️ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    panic_sentinel()
