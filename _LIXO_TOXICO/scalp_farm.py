import os
import time
import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# --- FARM CONFIG (HIGH VOLUME MODE - SUSTAINABLE) ---
CAPITAL_PER_TRADE = 200 # Margin of $200 -> Notional $2000 at 10x
LEVERAGE = 10 # High Leverage for Volume
TP_PCT = 0.05 # 5% Base Target (Partial Exit)
SL_PCT = 0.02 # 2% Structural Stop ($40 Risk if Notional $2k)
LOCKOUT_DURATION = 600 
REFRESH_INTERVAL = 300 
TRAILING_ACTIVATION = 0.015 # 1.5% Trailing
# ------------------------------

load_dotenv()

class ScalpFarm:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        self.active_symbols = []
        self.lockout_timers = {} # Symbol -> Timestamp (When lockout ends)
        self.target_assets = [] # Dynamic List
        self.last_refresh = 0
        
        # --- PRECISION MANAGER & LIMITS ---
        self.market_precisions = {} # {symbol: {'tickSize': 0.01, 'stepSize': 1.0}}
        self.MAX_OPEN_POSITIONS = 3 # Risk Limit
        self._init_precisions()

    def _init_precisions(self):
        """
        Initializes precision map for all markets to avoid API errors.
        """
        try:
            print("   ️ Initializing Precision Manager...")
            markets = self.data.get_markets()
            for m in markets:
                symbol = m.get('symbol')
                filters = m.get('filters', {})
                price_filter = filters.get('price', {})
                qty_filter = filters.get('quantity', {})
                
                self.market_precisions[symbol] = {
                    'tickSize': float(price_filter.get('tickSize', '0.01')),
                    'stepSize': float(qty_filter.get('stepSize', '1.0'))
                }
            print(f"    Loaded Precision Data for {len(self.market_precisions)} markets.")
        except Exception as e:
            print(f"   ️ Precision Init Failed: {e}")

    def get_tick_size(self, symbol):
        # Optimized lookup from memory
        if symbol in self.market_precisions:
            return self.market_precisions[symbol]['tickSize']
        return 0.01 # Fallback

    def get_step_size(self, symbol):
        if symbol in self.market_precisions:
            return self.market_precisions[symbol]['stepSize']
        return 1.0

    def round_to_step(self, qty, step_size):
        if step_size < 1:
            precision = int(round(-np.log10(step_size), 0))
            return round(qty, precision)
        else:
            return int(qty // step_size) * step_size

    def round_to_tick(self, price, tick_size):
        if tick_size < 1:
            precision = int(round(-np.log10(tick_size), 0))
            return round(price, precision)
        else:
            return round(price / tick_size) * tick_size

    def log_decision(self, actor, action, symbol, reason, details=""):
        """
        Unified Decision Log for Audit
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{actor}] {action} on {symbol} | Reason: {reason} | {details}\n"
        
        try:
            with open("decision_log.txt", "a") as f:
                f.write(log_entry)
            # print(f"    Logged: {action} on {symbol}")
        except Exception as e:
            print(f"   ️ Failed to write log: {e}")

    def calculate_golden_score(self, ticker, funding_rate, klines):
        """
        Calculates the 'Golden Equation' Score for an asset.
        Score = Funding(40%) + RSI_Dev(30%) + Volume(30%)
        """
        try:
            # 1. Volume Score
            volume = float(ticker['quoteVolume'])
            if volume < 1_000_000: return 0 # Ignore low volume
            norm_vol = min(np.log10(volume / 1_000_000), 3.0)
            
            # 2. RSI Score
            closes = [float(k['close']) for k in klines]
            rsi = self.indicators.calculate_rsi(pd.DataFrame({'close': closes})).iloc[-1]
            rsi_dev = abs(rsi - 50)
            norm_rsi = min(rsi_dev / 20.0, 2.0)
            
            # 3. Funding Score
            funding = funding_rate * 100 # Percentage
            norm_funding = min(abs(funding) / 0.05, 2.0)
            
            # Weighted Sum
            raw_score = (norm_funding * 40) + (norm_rsi * 30) + (norm_vol * 30)
            return raw_score, rsi
        except:
            return 0, 50

    def refresh_opportunity_pool(self):
        print("\n REFRESHING OPPORTUNITY POOL (Golden Equation)...")
        try:
            # Fetch all markets
            tickers = self.data.get_tickers()
            mark_prices = self.data.get_mark_prices()
            
            if not tickers or not mark_prices:
                print("   ️ Failed to fetch market data. Keeping existing list.")
                return

            # Map Data
            ticker_map = {t['symbol']: t for t in tickers}
            funding_map = {m['symbol']: float(m.get('fundingRate', 0)) for m in mark_prices}
            
            perp_markets = [s for s in ticker_map.keys() if 'PERP' in s]
            scored_assets = []
            
            print(f"    Scanning {len(perp_markets)} assets for Volatility & Volume...")
            
            for symbol in perp_markets:
                # Basic Pre-filter to save API calls
                ticker = ticker_map.get(symbol)
                if float(ticker['quoteVolume']) < 1_000_000: continue
                
                # Get Klines for RSI (Need minimal history)
                # Optimization: We can't fetch klines for ALL 100+ pairs quickly.
                # Heuristic: Focus on Top Volume first or iterate slowly?
                # For now, let's pick Top 30 by Volume to analyze deeply.
                pass 
            
            # Sort by Volume first to pick candidates for Deep Scan
            perp_markets.sort(key=lambda s: float(ticker_map[s]['quoteVolume']), reverse=True)
            candidates = perp_markets[:25] # Top 25 Volume Assets
            
            for symbol in candidates:
                klines = self.data.get_klines(symbol, "1h", limit=30)
                if not klines: continue
                
                score, rsi = self.calculate_golden_score(ticker_map[symbol], funding_map.get(symbol, 0), klines)
                
                if score > 50: # Minimum score threshold
                    scored_assets.append({'symbol': symbol, 'score': score, 'rsi': rsi})
                    # print(f"       {symbol}: Score {score:.1f} | RSI {rsi:.1f}")

            # Sort by Score
            scored_assets.sort(key=lambda x: x['score'], reverse=True)
            
            # Update Target List (Top 10)
            # self.target_assets = [item['symbol'] for item in scored_assets[:12]]
            
            # print(f"    NEW TARGET POOL ({len(self.target_assets)}):")
            # for item in scored_assets[:5]:
            #     print(f"      ⭐ {item['symbol']} (Score: {item['score']:.1f})")
                
            # Always include user favorites if not present
            # favorites = ["SOL_USDC_PERP", "FOGO_USDC_PERP", "ETH_USDC_PERP"]
            # for fav in favorites:
            #     if fav not in self.target_assets:
            #         self.target_assets.append(fav)
                    # print(f"       Added Favorite: {fav}")
            
            # RESTRICT TO SOL AND BTC ONLY (USER ORDER - RESCUE PROTOCOL)
            self.target_assets = ["SOL_USDC_PERP", "BTC_USDC_PERP"]
            print(f"    RESCUE PROTOCOL ACTIVE: Restricted to {self.target_assets}")
            
            self.last_refresh = time.time()
            
        except Exception as e:
            print(f"    Error refreshing pool: {e}")
            # Fallback list if empty
            if not self.target_assets:
                self.target_assets = ["SOL_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP"]

    def run(self):
        print(f" SCALP FARM ACTIVE | ${CAPITAL_PER_TRADE} | {LEVERAGE}x")
        print(f"   Strategy: MAKER ONLY (Post Only) | Target: {TP_PCT*100}% | Stop: {SL_PCT*100}%")
        print(f"   ️ Guardian Lockout: {LOCKOUT_DURATION/60} min cooldown on failure")
        print(f"    Dynamic Pool: Refresh every {REFRESH_INTERVAL}s based on Golden Equation")
        
        # Initial Refresh
        self.refresh_opportunity_pool()
        
        while True:
            try:
                # Check for Refresh
                if time.time() - self.last_refresh > REFRESH_INTERVAL:
                    self.refresh_opportunity_pool()

                print(f"\n Scanning Field ({len(self.target_assets)} Assets)...")
                
                # Check Max Positions
                positions = self.data.get_positions()
                open_count = len([p for p in positions if float(p['netQuantity']) != 0])
                
                if open_count >= self.MAX_OPEN_POSITIONS:
                    print(f"    Max Positions Reached ({open_count}/{self.MAX_OPEN_POSITIONS}). Waiting for exit.")
                    time.sleep(30)
                    continue

                for symbol in self.target_assets:
                    if symbol not in self.active_symbols:
                        self.farm_asset(symbol)
                        time.sleep(0.5) # Rate Limit Guard
                
                print(" Resting Field (30s)...")
                time.sleep(30)
                
            except Exception as e:
                print(f"️ Farm Loop Error: {e}")
                time.sleep(5)

    def farm_asset(self, symbol):
        try:
            # 1. Check Lockout
            if symbol in self.lockout_timers:
                remaining = self.lockout_timers[symbol] - time.time()
                if remaining > 0:
                    # print(f"   ️ {symbol} in Cooling Off ({int(remaining)}s left). Skipping.")
                    return
                else:
                    del self.lockout_timers[symbol] # Lockout expired
                    print(f"    {symbol} Cooling Off Expired. Re-engaging.")

            # 2. Check if already positioned
            positions = self.data.get_positions()
            pos = next((p for p in positions if p['symbol'] == symbol and float(p['netQuantity']) != 0), None)
            
            if pos:
                if symbol not in self.active_symbols:
                    self.active_symbols.append(symbol)
                    print(f"   Existing Position in {symbol}. Added to monitoring.")
                return

            # 3. Analyze for Entry Direction
            # TREND FILTER (1h Timeframe) - CRITICAL: Don't fight the trend
            klines_1h = self.data.get_klines(symbol, interval="1h", limit=50)
            trend_direction = "NEUTRAL"
            if klines_1h:
                df_1h = pd.DataFrame(klines_1h)
                df_1h['close'] = df_1h['close'].astype(float)
                ema_50 = df_1h['close'].ewm(span=50).mean().iloc[-1]
                current_price_1h = df_1h['close'].iloc[-1]
                
                if current_price_1h < ema_50:
                    trend_direction = "DOWN"
                else:
                    trend_direction = "UP"
            
            # Micro Analysis (5m)
            klines = self.data.get_klines(symbol, interval="5m", limit=50)
            if not klines: return
            
            df = pd.DataFrame(klines)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            # Spread Check (Crucial for farming)
            ticker = self.data.get_ticker(symbol)
            
            # Safe Fetch
            if 'bestBid' not in ticker:
                # Try Depth
                depth = self.data.get_orderbook_depth(symbol)
                if not depth or not depth['bids']: return
                best_bid = float(depth['bids'][0][0])
                best_ask = float(depth['asks'][0][0])
            else:
                best_bid = float(ticker['bestBid'])
                best_ask = float(ticker['bestAsk'])
                
            spread_pct = (best_ask - best_bid) / best_bid
            
            if spread_pct > 0.001: # Skip if spread > 0.1% (Too expensive/risky)
                # print(f"    {symbol} Spread too wide ({spread_pct*100:.3f}%). Skipping.")
                return
                
            rsi = self.indicators.calculate_rsi(df).iloc[-1]
            bb = self.indicators.calculate_bollinger_bands(df)
            price = df['close'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            upper = bb['upper'].iloc[-1]
            
            # Logic: Mean Reversion ALIGNED WITH TREND
            signal = None
            side = None
            
            # Filter Logic:
            # If Trend DOWN -> ONLY SHORT (Sell Rallies at Upper Band)
            # If Trend UP -> ONLY LONG (Buy Dips at Lower Band)
            
            if trend_direction == "UP":
                if price <= lower * 1.002: # Near Lower Band
                    signal = "LONG (Trend Following)"
                    side = "Bid"
                elif price >= upper:
                    # Counter-trend Short? NO.
                    pass
            elif trend_direction == "DOWN":
                if price >= upper * 0.998: # Near Upper Band
                    signal = "SHORT (Trend Following)"
                    side = "Ask"
                elif price <= lower:
                    # Counter-trend Long? NO.
                    pass
                
            # If no signal, don't force it. Wait for edge.
            if not signal:
                return

            print(f"    {symbol}: {signal} | Trend: {trend_direction} | Spread: {spread_pct*100:.3f}%")
            self.execute_maker_trade(symbol, side, signal)
            
        except Exception as e:
            print(f"   ️ Error farming {symbol}: {e}")

    def execute_maker_trade(self, symbol, side, signal_reason):
        print(f" PLANTING SEED (MAKER) on {symbol}...")
        
        # Robust Price Fetch
        ticker = self.data.get_ticker(symbol)
        if 'bestBid' in ticker:
            best_bid = float(ticker['bestBid'])
            best_ask = float(ticker['bestAsk'])
        else:
            depth = self.data.get_orderbook_depth(symbol)
            if not depth or not depth['bids']: return
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            
        # Maker Price Strategy: Join the Best Bid/Ask + Tick (Aegis Smart Limit)
        
        # Get Tick Size
        tick_size = self.get_tick_size(symbol)
        
        if side == "Bid":
            price = best_bid + tick_size
            if price >= best_ask: price = best_bid
        else:
            price = best_ask - tick_size
            if price <= best_bid: price = best_ask
        
        # Round Price to Tick Size
        price = self.round_to_tick(price, tick_size)
        
        # Quantity
        notional = CAPITAL_PER_TRADE * LEVERAGE
        qty = notional / price
        
        # Rounding Logic (Optimized for Memecoins)
        if "PEPE" in symbol or "SHIB" in symbol or "BONK" in symbol or "FOGO" in symbol or "DOGE" in symbol or "WIF" in symbol or "MON" in symbol:
            qty = int(qty)
        elif "LDO" in symbol: # LDO specific fix
            qty = int(qty)
        elif price > 1000: 
            qty = round(qty, 3)
        else: 
            qty = round(qty, 1)

        try:
            # POST ONLY IS MANDATORY FOR FARMING
            print(f"   Attempting Post-Only Limit @ {price}")
            order = self.trade.execute_order(
                symbol=symbol,
                side=side,
                order_type="Limit",
                quantity=str(qty),
                price=str(price),
                post_only=True
            )
            
            if not order:
                print("   ️ Post-Only Rejected (Price Moved). Retrying next cycle.")
                return

            print(f"    Order Planted: {order.get('id')}")
            
            # LOG ENTRY
            self.log_decision("SCALP_BOT", "OPEN_ORDER", symbol, signal_reason, f"Side: {side} | Price: {price} | Qty: {qty}")
            
            # Monitor Fill & Activate Guardian Protocol
            self.monitor_and_protect(symbol, order.get('id'), side, price, qty)
            
        except Exception as e:
            print(f" Farming Failed: {e}")

    def get_tick_size(self, symbol):
        # Optimized lookup from memory
        if symbol in self.market_precisions:
            return self.market_precisions[symbol]['tickSize']
        
        # Fallback Heuristic
        if "PEPE" in symbol or "SHIB" in symbol or "BONK" in symbol or "FOGO" in symbol or "MON" in symbol: return 0.000001
        return 0.01

    def monitor_and_protect(self, symbol, order_id, side, entry_price, qty):
        # OPTIMIZED: Quick Check (6s)
        
        print("    Watching for Sprout (Fill) - Quick Check...")
        filled = False
        
        for _ in range(3): # Check for 6 seconds
            time.sleep(2)
            orders = self.data.get_open_orders()
            my_order = next((o for o in orders if o['id'] == order_id), None)
            
            if not my_order:
                # Order gone -> Filled or Cancelled
                positions = self.data.get_positions()
                pos = next((p for p in positions if p['symbol'] == symbol and float(p['netQuantity']) != 0), None)
                
                if pos:
                    print("    SEED SPROUTED (Filled)!")
                    filled = True
                    entry_price = float(pos['entryPrice'])
                    
                    # LOG FILL
                    self.log_decision("SNIPER_BOT", "FILLED", symbol, "Order Executed", f"Entry: {entry_price}")
                    break
                else:
                     print("   ️ Order Cancelled/Expired.")
                     return
        
        if not filled:
            print("   ️ Seed didn't sprout (Timeout). Cancelling to move fast...")
            self.trade.cancel_open_orders(symbol)
            return

        # --- GUARDIAN PROTOCOL (ATOMIC PROTECTION) ---
        print(f"   ️ ACTIVATING GUARDIAN PROTOCOL for {symbol}...")
        
        # Get Tick Size
        tick_size = self.get_tick_size(symbol)
        
        # SL Logic (2%)
        raw_sl = entry_price * (1 - SL_PCT) if side == "Bid" else entry_price * (1 + SL_PCT)
        sl_price = self.round_to_tick(raw_sl, tick_size)
        
        # TP Logic (5% - Partial Exit)
        raw_tp = entry_price * (1 + TP_PCT) if side == "Bid" else entry_price * (1 - TP_PCT)
        tp_price = self.round_to_tick(raw_tp, tick_size)
        
        # Format for API
        sl_str = "{:.10f}".format(sl_price).rstrip('0').rstrip('.')
        tp_str = "{:.10f}".format(tp_price).rstrip('0').rstrip('.')
        
        # Exit Side
        exit_side = "Ask" if side == "Bid" else "Bid"
        
        protection_success = False
        
        # Retry Loop for Protection
        for attempt in range(3):
            try:
                print(f"      ️ Attempt {attempt+1}: Placing SL @ {sl_str}...")
                sl_order = self.trade.execute_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="Market", # Stop Market
                    quantity=str(qty),
                    price=None,
                    trigger_price=sl_str
                )
                
                if sl_order and sl_order.get('id'):
                    print(f"       SL LOCKED: {sl_order.get('id')}")
                    protection_success = True
                    
                    # Place TP 1 (50% Quantity)
                    half_qty = qty / 2
                    if half_qty < 1 and price > 1000: half_qty = round(half_qty, 3)
                    elif half_qty >= 1: half_qty = int(half_qty)
                    
                    tp_order = self.trade.execute_order(
                        symbol=symbol,
                        side=exit_side,
                        order_type="Limit",
                        quantity=str(half_qty),
                        price=tp_str,
                        post_only=True # MAKER ONLY EXIT
                    )
                    print(f"       TP1 (50%) PLACED: {tp_str}")
                    
                    # LOG PROTECTION
                    self.log_decision("SNIPER_BOT", "PROTECTION_PLACED", symbol, "Guardian Protocol", f"SL: {sl_str} | TP1: {tp_str}")
                    break
                else:
                    print("      ️ SL Placement Failed. Retrying...")
                    time.sleep(1)
            except Exception as e:
                print(f"       Error placing SL: {e}")
                time.sleep(1)
                
        if not protection_success:
            print("    GUARDIAN ALERT: PROTECTION FAILED! EXECUTING EMERGENCY EXIT!")
            # Emergency Close
            self.trade.close_position(symbol, float(pos['netQuantity']))
            print("   ️ POSITION KILLED FOR SAFETY.")
            
            # ACTIVATE LOCKOUT
            self.lockout_timers[symbol] = time.time() + LOCKOUT_DURATION
            self.log_decision("SNIPER_BOT", "EMERGENCY_EXIT", symbol, "Protection Failure", f"Lockout activated for {LOCKOUT_DURATION}s")

        else:
            print("    Sniper Position Secured.")
            self.active_symbols.append(symbol)

if __name__ == "__main__":
    farm = ScalpFarm()
    farm.run()
