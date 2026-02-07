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
LEVERAGE = 20
STOP_LOSS_PCT = 1.0  # 1% move against us = 20% loss (Acceptable for recovery attempt?)
TAKE_PROFIT_PCT = 2.0 # 2% move in favor = 40% profit
MAX_POSITIONS = 1

def flash_scalper():
    print(f"\n [FLASH SCALPER] 1-SECOND RECOVERY MODE")
    print("    TARGET: HIGH VOLATILITY DUMPS (MOMENTUM SHORTS)")
    print(f"   ️ LEVERAGE: {LEVERAGE}x | SL: {STOP_LOSS_PCT}%")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    
    while True:
        try:
            # 1. SCAN TICKERS (FAST)
            print("\n    Scanning Market Momentum...")
            tickers = data.get_tickers()
            if not tickers:
                time.sleep(1)
                continue
                
            perp_tickers = [t for t in tickers if t['symbol'].endswith('_PERP')]
            
            # Sort by % Change (Lowest first -> Top Losers)
            perp_tickers.sort(key=lambda x: float(x['priceChangePercent']))
            
            # Show Top 5 Losers
            print(f"\n   {'SYMBOL':<15} | {'CHANGE 24H':<10} | {'PRICE':<10}")
            print("-" * 45)
            for t in perp_tickers[:5]:
                print(f"   {t['symbol']:<15} | {float(t['priceChangePercent']):.2f}%     | ${float(t['lastPrice']):.4f}")
            print("-" * 45)
            
            # 2. SELECT BEST CANDIDATE (MICRO-SCALP 0.3% DROP)
            print("    Analyzing Micro-Drops (Scalp Mode)...")
            
            best_target = None
            max_drop = 0.0
            
            # DEBUG: Print first few drops to verify calculation
            debug_count = 0
            
            for t in perp_tickers:
                symbol = t['symbol']
                # Skip low volume
                if float(t['quoteVolume']) < 100_000: continue # Lower volume filter for alts
                
                try:
                    # Use Ticker Data (Instant)
                    high_24h = float(t['highPrice'])
                    curr_price = float(t['lastPrice'])
                    
                    if high_24h == 0: continue
                    
                    # Calculate Drop from Peak
                    drop_pct = (curr_price - high_24h) / high_24h * 100
                    
                    # Debug print for top losers
                    if drop_pct < -1.0 and debug_count < 3:
                         print(f"       {symbol}: Drop {drop_pct:.2f}% (Price: {curr_price})")
                         debug_count += 1
                    
                    # MICRO-SCALP TRIGGER: Down > 1.5% from High is enough for a scalp
                    if drop_pct < -1.5: 
                        # Check if it's the biggest drop
                        if drop_pct < max_drop:
                            max_drop = drop_pct
                            best_target = t
                            best_target['drop_pct'] = drop_pct
                except:
                    continue
            
            if not best_target:
                print("    No micro-crashes found (> -1.5%). Market is sleeping.")
                time.sleep(1) # Faster loop
                continue
                
            symbol = best_target['symbol']
            price = float(best_target['lastPrice'])
            print(f"\n    TARGET ACQUIRED: {symbol} (Drop: {best_target['drop_pct']:.2f}%)")
            
            # 3. VERIFY MICRO-MOMENTUM (1m Candle)
            # We want to enter when it's actively crashing, not consolidating.
            candles = data.get_klines(symbol, "1m", limit=5)
            if not candles: continue
            
            last_candle = candles[-1]
            prev_candle = candles[-2]
            
            # Check if last candle is RED
            open_p = float(last_candle['open'])
            close_p = float(last_candle['close'])
            
            if close_p < open_p:
                print("    MICRO-TREND: RED CANDLE (Continuing Down).")
                
                # 4. EXECUTE SHORT
                print(f"    EXECUTING 20X SHORT ON {symbol} (ATOMIC SAFE MODE)...")
                
                # Set Leverage (Optional, kept for safety)
                try:
                    trade.set_leverage(symbol, LEVERAGE)
                except:
                    pass 
                    
                # Calc Quantity ($100 Margin = $2000 Size)
                qty = 2000.0 / price
                # Precision check
                if price > 100:
                    qty = round(qty, 2)
                elif price > 1:
                    qty = round(qty, 1)
                else:
                    qty = int(qty)
                    
                # EXECUTE ORDER via SafeExecutor
                from safe_execution import SafeExecutor
                executor = SafeExecutor(symbol)
                
                # SL is STOP_LOSS_PCT (1.0) -> 0.01
                try:
                    executor.execute_atomic_order("Sell", qty, LEVERAGE, sl_pct=STOP_LOSS_PCT/100)
                    print(f"    ORDER SENT! Protection Active.")
                except SystemExit:
                     print("    SYSTEM EXIT TRIGGERED BY SAFE EXECUTOR.")
                     continue
                except Exception as e:
                     print(f"    EXECUTION FAILED: {e}")
                     continue

                # 5. MONITOR FOR PROFIT (TP)
                # Sentinel handles SL. We handle TP.
                entry_price = price
                tp_price = entry_price * (1 - TAKE_PROFIT_PCT/100)
                
                print(f"    MANAGING PROFIT. TP: {tp_price:.4f} (SL handled by Sentinel/SafeExecutor)")
                
                while True:
                    ticker = data.get_ticker(symbol)
                    curr_price = float(ticker['lastPrice'])
                    
                    pnl = (entry_price - curr_price) / entry_price * 100 * LEVERAGE
                    print(f"    PnL: {pnl:.2f}% | Price: {curr_price:.4f}", end="\r")
                    
                    # TAKE PROFIT
                    if curr_price <= tp_price:
                        print(f"\n    TAKE PROFIT HIT! Closing...")
                        trade.execute_order(symbol, "Bid", 0, qty, order_type="Market")
                        break
                    
                    # Check if stopped out (Price > SL) - Loop will break if position is closed?
                    # We can check position status
                    # But for now, simple price check is enough to stop the loop
                    if curr_price >= entry_price * (1 + STOP_LOSS_PCT/100):
                         print(f"\n    Appears Stopped Out. Exiting Loop.")
                         break
                         
                    time.sleep(1)
                
                break # Exit after 1 trade to avoid overtrading
                
            else:
                print("    Last candle is GREEN. Waiting for red candle to Short...")
                time.sleep(2)
        
        except Exception as e:
            print(f"   ️ Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    flash_scalper()
