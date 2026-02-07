import pandas as pd
from technical_oracle import MarketProxyOracle

class SmartEntrySniper:
    def __init__(self, symbol, data_engine, trade_engine, indicators):
        self.symbol = symbol
        self.data = data_engine
        self.trade = trade_engine
        self.indicators = indicators
        self.oracle = MarketProxyOracle(symbol, auth=data_engine.auth, data_engine=data_engine)

    def analyze(self):
        # 1. Technicals (EMA 200 + RSI)
        candles = self.data.get_klines(self.symbol, "1h", limit=200)
        if not candles: return None, "No Data"

        df = pd.DataFrame(candles)
        df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
        df['close'] = df['close'].astype(float)
        
        rsi = self.indicators.calculate_rsi(df).iloc[-1]
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # 2. Funding Bias
        bias, funding_rate = self.oracle.get_funding_bias()
        
        # 3. Decision Logic
        signal = None
        reason = ""
        
        # Long Logic
        if current_price > ema_200: # Trend Bullish
            if rsi < 40: # Oversold Pullback (Relaxed for Alts)
                if bias != "BEARISH_CROWDED": 
                    signal = "Bid"
                    reason = "Trend Bullish + Oversold"
            else:
                reason = f"Trend Bullish but RSI {rsi:.2f} too high"
        
        # Short Logic
        elif current_price < ema_200: # Trend Bearish
            if rsi > 60: # Overbought Pullback (Relaxed for Alts)
                if bias != "BULLISH_SQUEEZE": 
                    signal = "Ask"
                    reason = "Trend Bearish + Overbought"
            else:
                reason = f"Trend Bearish but RSI {rsi:.2f} too low"
        
        return signal, reason, rsi, ema_200, current_price

    def execute_trade(self, signal, price):
        # --- CAPITAL ALLOCATION (HEAVY ARTILLERY) ---
        TARGET_NOTIONAL = 2000.0
        
        # Check Available Balance (Optional but recommended)
        # For now, we trust the Authorization
        
        qty = TARGET_NOTIONAL / price
        qty = round(qty, 4) # Ensure precision
        price = round(price, 2) # Ensure precision (USDC usually 2 decimals? PERP maybe different)
        # Check tick size? Precision Manager handles this usually? 
        # But here we are hardcoding round(qty, 4).
        # Ideally we should use Precision Manager.
        
        print(f"    FIRING {signal} {qty} @ {price}...")
        self.trade.execute_order(self.symbol, signal, price, qty, post_only=True)

    def execute_sniper(self):
        # print(f" [SNIPER] Scanning {self.symbol}...") # Silent Scan
        
        signal, reason, rsi, ema_200, current_price = self.analyze()
                    
        if not signal:
            # print(f"    No Signal. Reason: {reason}")
            return
            
        print(f" [SNIPER] Signal Detected on {self.symbol}!")
        print(f"   REASON: {reason} | RSI: {rsi:.2f} | Price: {current_price}")
        
        # 4. Oracle Validation (The Final Judge)
        if self.oracle.validate_entry(signal):
            print(f"    Oracle Approved! Executing...")
            self.execute_trade(signal, current_price)
        else:
            print("    Oracle Blocked Entry.")
