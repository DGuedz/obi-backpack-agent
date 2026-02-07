import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

# --- NIGHT OWL CONFIG ---
CAPITAL_PER_TRADE = 1000 # UPGRADED TO $1000
LEVERAGE = 10
STOP_LOSS_PCT = 0.02  # 2%
TAKE_PROFIT_PCT = 0.05 # 5%
# ------------------------

load_dotenv()

class NightOwlSniper:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        self.active_symbols = [] # Track what we are already in

    def scan_and_execute(self):
        print(f" NIGHT OWL SNIPER ACTIVE | ${CAPITAL_PER_TRADE} | {LEVERAGE}x")
        print(f"️ GUARDIAN PROTOCOL: ON (SL: {STOP_LOSS_PCT*100}% | TP: {TAKE_PROFIT_PCT*100}%)")
        
        while True:
            try:
                # 1. Update Market List
                # Focus on liquid perps
                markets = self.data.get_markets()
                candidates = [m['symbol'] for m in markets if 'USDC_PERP' in m['symbol']]
                
                # Filter for Volume (Optimization)
                # In a real loop, we might cache this. For now, we pick a subset or scan all slowly.
                # Let's pick top volume/volatility candidates from a quick ticker check.
                tickers = self.data.get_tickers()
                # Sort by Quote Volume
                sorted_tickers = sorted(tickers, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
                top_20 = [t['symbol'] for t in sorted_tickers[:20]]
                
                print(f" Scanning Top 20 Assets for Opportunities...")
                
                for symbol in top_20:
                    if symbol in self.active_symbols:
                        continue # Skip if already in
                        
                    self.analyze_asset(symbol)
                    time.sleep(1) # Rate limit respect
                
                print(" Scan complete. Resting 30s...")
                time.sleep(30)
                
            except Exception as e:
                print(f"️ Scan Error: {e}")
                time.sleep(10)

    def analyze_asset(self, symbol):
        try:
            klines = self.data.get_klines(symbol, interval="15m", limit=50)
            if not klines: return

            df = pd.DataFrame(klines)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            rsi = self.indicators.calculate_rsi(df).iloc[-1]
            bb = self.indicators.calculate_bollinger_bands(df)
            
            price = df['close'].iloc[-1]
            upper = bb['upper'].iloc[-1]
            lower = bb['lower'].iloc[-1]
            sma = bb['middle'].iloc[-1]
            
            # Trend Detection
            trend = "BULL" if price > sma else "BEAR"
            
            # --- STRATEGY LOGIC ---
            signal = None
            side = None
            
            # 1. Bearish Scalp (Rally in Bear Trend)
            # RSI > 60 in Bear Trend + Price touching Upper Band?
            if trend == "BEAR" and rsi > 65:
                signal = "SHORT (Bear Rally)"
                side = "Ask"
                
            # 2. Bullish Scalp (Dip in Bull Trend)
            # RSI < 35 in Bull Trend
            elif trend == "BULL" and rsi < 35:
                signal = "LONG (Bull Dip)"
                side = "Bid"
                
            # 3. Extreme Reversion (Any Trend)
            elif rsi < 20:
                signal = "LONG (Oversold)"
                side = "Bid"
            elif rsi > 80:
                signal = "SHORT (Overbought)"
                side = "Ask"
                
            if signal:
                print(f"    {symbol}: {signal} | RSI {rsi:.1f}")
                self.execute_trade_with_guardian(symbol, side, price)
                self.active_symbols.append(symbol)
                
        except Exception as e:
            print(f"   ️ Error analyzing {symbol}: {e}")

    def execute_trade_with_guardian(self, symbol, side, price):
        print(f" EXECUTING {side} on {symbol}...")
        
        # 1. Calculate Quantity
        ticker = self.data.get_ticker(symbol)
        
        # Safe Price Fetch
        if 'bestAsk' in ticker and 'bestBid' in ticker:
            best_price = float(ticker['bestAsk']) if side == "Bid" else float(ticker['bestBid'])
        else:
            # Fallback to Depth
            print("   ️ Ticker missing bestBid/Ask. Checking Depth...")
            depth = self.data.get_orderbook_depth(symbol)
            if depth and depth['bids'] and depth['asks']:
                best_price = float(depth['asks'][0][0]) if side == "Bid" else float(depth['bids'][0][0])
            else:
                print("    Depth Failed. Aborting.")
                return

        notional = CAPITAL_PER_TRADE * LEVERAGE
        qty = notional / best_price
        
        # Adjust Step Size (Crucial)
        # We need step size from market info. Assuming 1 or 0.1 for most.
        # For safety/speed, using integer for large qtys or 1 decimal.
        # Ideally fetch 'filters' from get_markets.
        # Quick hack: If price < 1, qty int. If price > 1000, qty 3 decimals.
        # Better: check step size.
        # Let's default to int() for now to be safe on most alts, unless price is huge (BTC).
        if best_price > 1000:
            qty = round(qty, 3)
        else:
            qty = int(qty)
            
        print(f"   Qty: {qty} @ {best_price}")
        
        # 2. Execute Entry (Limit IOC or Market for speed?)
        # User said "Tiro Certo" -> Limit Post Only is safer for fees, but "Market" ensures entry.
        # Let's use Limit at slightly aggressive price to ensure fill.
        limit_price = best_price * 1.001 if side == "Bid" else best_price * 0.999
        
        # Rounding Heuristic (Safety for "Price decimal too long")
        if limit_price > 1000:
            limit_price = round(limit_price, 1)
        elif limit_price > 1:
            limit_price = round(limit_price, 2)
        else:
            limit_price = round(limit_price, 6)
            
        try:
            order = self.trade.execute_order(
                symbol=symbol,
                side=side,
                order_type="Limit",
                quantity=str(qty),
                price=str(limit_price)
            )
            print(f"    Entry Sent: {order.get('id')}")
            
            # 3. GUARDIAN PROTOCOL (Immediate SL/TP)
            time.sleep(2) # Wait for fill/book
            
            # SL
            sl_trigger = best_price * (1 - STOP_LOSS_PCT) if side == "Bid" else best_price * (1 + STOP_LOSS_PCT)
            # Robust Rounding
            if sl_trigger >= 1000: sl_trigger = round(sl_trigger, 1)
            elif sl_trigger >= 10: sl_trigger = round(sl_trigger, 2)
            elif sl_trigger >= 1: sl_trigger = round(sl_trigger, 4)
            else: sl_trigger = round(sl_trigger, 6)
            
            # TP
            tp_price = best_price * (1 + TAKE_PROFIT_PCT) if side == "Bid" else best_price * (1 - TAKE_PROFIT_PCT)
            # Robust Rounding
            if tp_price >= 1000: tp_price = round(tp_price, 1)
            elif tp_price >= 10: tp_price = round(tp_price, 2)
            elif tp_price >= 1: tp_price = round(tp_price, 4)
            else: tp_price = round(tp_price, 6)
            
            # Place SL (Market Trigger)
            print(f"   ️ Placing SL @ {sl_trigger}")
            self.trade.execute_order(
                symbol=symbol,
                side="Ask" if side == "Bid" else "Bid",
                order_type="Market",
                quantity=str(qty),
                price=None,
                trigger_price=str(sl_trigger)
            )
            
            # Place TP (Limit)
            print(f"    Placing TP @ {tp_price}")
            self.trade.execute_order(
                symbol=symbol,
                side="Ask" if side == "Bid" else "Bid",
                order_type="Limit",
                quantity=str(qty),
                price=str(tp_price)
            )
            
            print(f"    {symbol} ARMORED.")
            
        except Exception as e:
            print(f" Execution Failed: {e}")

if __name__ == "__main__":
    bot = NightOwlSniper()
    bot.scan_and_execute()
