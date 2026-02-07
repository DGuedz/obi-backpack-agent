import pandas as pd
import numpy as np

class AdvancedIndicators:
    def __init__(self, data_module):
        self.data = data_module

    def analyze_spread(self, symbol):
        """
        Calculates Spread efficiency.
        Spread = (Ask - Bid) / Ask * 10000 (Basis Points)
        """
        try:
            ticker = self.data.get_ticker(symbol) # Ensure get_ticker is available or fallback
            if not ticker:
                # Try order book
                book = self.data.get_order_book(symbol)
                if not book or not book.get('bids') or not book.get('asks'):
                    return 0.0
                bid = float(book['bids'][0][0])
                ask = float(book['asks'][0][0])
            else:
                # Some tickers don't have bid/ask, only lastPrice. Check structure.
                # If ticker has 'bestBid' and 'bestAsk' (Backpack usually does)
                bid = float(ticker.get('bestBid', 0))
                ask = float(ticker.get('bestAsk', 0))
                if bid == 0 or ask == 0:
                     # Fallback to book
                     book = self.data.get_order_book(symbol)
                     if book and book.get('bids') and book.get('asks'):
                         bid = float(book['bids'][0][0])
                         ask = float(book['asks'][0][0])
                     else:
                         return 0.0
            
            spread_bps = ((ask - bid) / ask) * 10000
            return spread_bps
        except:
            return 0.0

    def get_backpack_specific_metrics(self, symbol):
        """
        Fetches Backpack-specific fundamentals:
        1. Basis Yield (Annualized)
        2. Utilization Rate (Risk)
        """
        metrics = {
            'basis_yield_apr': 0.0,
            'utilization_rate': 0.0,
            'funding_rate_hourly': 0.0
        }
        
        try:
            # 1. Funding
            ticker = self.data.get_ticker(symbol)
            if ticker:
                funding = float(ticker.get('fundingRate', 0))
                metrics['funding_rate_hourly'] = funding
                
            # 2. Lending Stats (Utilization & Lend APY)
            lending_markets = self.data.get_borrow_lending_markets()
            # Find the asset (e.g. USDC for Collateral or the Token for Shorting)
            # Usually Utilization refers to the ASSET being borrowed.
            # If Longing PERP: We care about USDC Utilization (if borrowing margin)? 
            # Or is it just general system health?
            # User said: "Utilization Rate... of the available assets in the lending pool"
            # If we are Longing Perps, we are implicitly borrowing USDC (or using it as collateral).
            # If Shorting, we might be borrowing the asset if Spot, but Perps are synthetic.
            # However, Backpack "Interest Bearing Perps" might link Spot Borrowing rates to Perps.
            # Let's assume we check the Quote Asset (USDC) utilization as a system risk proxy.
            
            usdc_stats = next((m for m in lending_markets if m.get('symbol') == 'USDC'), None)
            if usdc_stats:
                utilization = float(usdc_stats.get('utilization', 0))
                lend_apy = float(usdc_stats.get('lendRate', 0)) # Check API key
                metrics['utilization_rate'] = utilization * 100 # %
                
                # Basis Yield Calculation
                # Basis Yield = Lend APY + (Funding * 24 * 365)
                # If Funding is negative (paying longs), it adds to Yield.
                # If Funding is positive (paying shorts), it subtracts for Longs.
                # Strategy: Yield Hunter (Long Bias) -> We want Negative Funding.
                # Yield = Lend APY + (-Funding * 24 * 365) ?? 
                # Actually, usually "Basis Trade" is Long Spot + Short Perp.
                # But here we are doing "Perp Yield Farming".
                # Yield = (-Funding * 24 * 365) if just holding Perp Long.
                # If we hold USDC as collateral, we get Lend APY on that USDC?
                # Backpack says: "Interest Bearing Perps".
                # Let's sum them: APR = (Funding * 24 * 365 * -1)  [If Long]
                
                metrics['basis_yield_apr'] = (funding * 24 * 365 * -1 * 100) # Simple APR from Funding
                
        except Exception as e:
            print(f"Error metrics: {e}")
            
        return metrics

    def analyze_order_book_imbalance(self, symbol, depth_limit=20):
        """
        Calculates Order Book Imbalance (OBI).
        OBI = (BidVol - AskVol) / (BidVol + AskVol)
        Range: -1 (Bearish) to +1 (Bullish)
        Also detects Sell Walls (Liquidity Walls).
        """
        try:
            depth = self.data.get_orderbook_depth(symbol, limit=depth_limit)
            if not depth or 'asks' not in depth or 'bids' not in depth:
                return 0.0
            
            bids = depth['bids']
            asks = depth['asks']
            
            bid_vol = sum([float(x[1]) for x in bids])
            ask_vol = sum([float(x[1]) for x in asks])
            
            if (bid_vol + ask_vol) == 0: return 0.0
            
            obi = (bid_vol - ask_vol) / (bid_vol + ask_vol)
            return obi
        except Exception as e:
            print(f"Error OBI: {e}")
            return 0.0

    def get_sell_wall_distance(self, symbol, depth_limit=50):
        """
        Finds the nearest 'Sell Wall' (Ask Liquidity Spike).
        Returns price distance % to the wall.
        """
        try:
            depth = self.data.get_orderbook_depth(symbol, limit=depth_limit)
            if not depth or 'asks' not in depth: return None
            
            asks = depth['asks'] # [[price, qty], ...]
            avg_vol = sum([float(x[1]) for x in asks]) / len(asks)
            threshold = avg_vol * 3.0 # Wall = 3x average volume
            
            current_price = float(asks[0][0])
            
            for price, qty in asks:
                if float(qty) > threshold:
                    wall_price = float(price)
                    distance = (wall_price - current_price) / current_price
                    return wall_price, distance
            
            return None, None
        except:
            return None, None

    def analyze_hft_setup(self, symbol):
        """
        Advanced HFT Analysis (Bollinger + StochRSI + EMA).
        Replaces basic exhaustion setup.
        """
        try:
            klines = self.data.get_klines(symbol, '15m', limit=100)
            if not klines:
                return {'signal': 'NEUTRAL', 'score': 0, 'rsi': 50}

            closes = [float(k.get('close') if isinstance(k, dict) else k[4]) for k in klines]
            series = pd.Series(closes)
            
            # 1. EMA 100 (Trend Filter)
            ema100 = series.ewm(span=100).mean().iloc[-1]
            current_price = closes[-1]
            trend = "BULL" if current_price > ema100 else "BEAR"
            
            # 2. Stochastic RSI
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            min_rsi = rsi.rolling(window=14).min()
            max_rsi = rsi.rolling(window=14).max()
            stoch = ((rsi - min_rsi) / (max_rsi - min_rsi)) * 100
            k_line = stoch.rolling(window=3).mean().iloc[-1]
            d_line = k_line # Simplified or add smoothing
            
            # 3. Bollinger Bands
            sma = series.rolling(20).mean()
            std = series.rolling(20).std()
            upper = sma + (std * 2)
            lower = sma - (std * 2)
            
            bb_width = (upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1]
            
            signal = "NEUTRAL"
            score = 0
            
            # Setup Logic
            # Long: Trend Bull + Stoch < 20 (Oversold) + Price near Lower BB
            if trend == "BULL" and k_line < 20:
                signal = "HFT_BUY_READY"
                score += 5
                if current_price <= lower.iloc[-1] * 1.01: # Near BB Low
                    score += 3
                    
            # Short: Trend Bear + Stoch > 80 (Overbought) + Price near Upper BB
            elif trend == "BEAR" and k_line > 80:
                signal = "HFT_SELL_READY"
                score += 5
                if current_price >= upper.iloc[-1] * 0.99: # Near BB High
                    score += 3
                    
            return {
                'signal': signal,
                'score': score,
                'stoch_k': k_line,
                'trend': trend,
                'bb_width': bb_width,
                'rsi': rsi.iloc[-1]
            }
            
        except Exception as e:
            print(f"Error HFT: {e}")
            return {'signal': 'ERROR', 'score': 0}

    def analyze_exhaustion_setup(self, symbol, timeframe='15m'):
        """
        Legacy wrapper for compatibility.
        """
        return self.analyze_hft_setup(symbol)

    def analyze_order_book_imbalance(self, symbol, depth=10):
        """
        Calculates Order Book Imbalance (OBI) to predict short-term price pressure.
        OBI = (BidQty - AskQty) / (BidQty + AskQty)
        Range: -1 (Strong Bearish) to +1 (Strong Bullish)
        """
        try:
            book = self.data.get_order_book(symbol)
            if not book: return 0.0
            
            bids = book.get('bids', [])[:depth]
            asks = book.get('asks', [])[:depth]
            
            bid_vol = sum([float(x[1]) for x in bids])
            ask_vol = sum([float(x[1]) for x in asks])
            
            if (bid_vol + ask_vol) == 0: return 0.0
            
            obi = (bid_vol - ask_vol) / (bid_vol + ask_vol)
            return obi
            
        except Exception as e:
            print(f"Error calculating OBI for {symbol}: {e}")
            return 0.0

    def analyze_liquidity_heatmap(self, symbol):
        """
        Identifies potential support/resistance based on large limit orders (Liquidity Walls).
        """
        try:
            book = self.data.get_order_book(symbol)
            if not book: return {}
            
            bids = book.get('bids', [])
            asks = book.get('asks', [])
            
            # Find largest walls
            max_bid = max(bids, key=lambda x: float(x[1])) if bids else [0, 0]
            max_ask = max(asks, key=lambda x: float(x[1])) if asks else [0, 0]
            
            return {
                'support_level': float(max_bid[0]),
                'support_vol': float(max_bid[1]),
                'resistance_level': float(max_ask[0]),
                'resistance_vol': float(max_ask[1])
            }
        except Exception:
            return {}
            
    def get_market_sentiment(self, symbol):
        """
        Combines OBI, Spread, and Wall analysis for a final verdict.
        """
        obi = self.analyze_order_book_imbalance(symbol)
        walls = self.analyze_liquidity_heatmap(symbol)
        
        signal = "NEUTRAL"
        strength = abs(obi)
        
        if obi > 0.2:
            signal = "BULLISH_PRESSURE"
        elif obi < -0.2:
            signal = "BEARISH_PRESSURE"
            
        return {
            'symbol': symbol,
            'obi_score': obi,
            'signal': signal,
            'walls': walls
        }

    def calculate_ema(self, data, period):
        """
        Calculates Exponential Moving Average (EMA).
        data: list of closing prices (floats)
        """
        if len(data) < period:
            return 0.0
        
        df = pd.DataFrame(data, columns=['close'])
        ema = df['close'].ewm(span=period, adjust=False).mean()
        return ema.iloc[-1]

    def calculate_rsi(self, data, period=14):
        """
        Calculates Relative Strength Index (RSI).
        data: list of closing prices (floats)
        """
        if len(data) < period + 1:
            return 50.0
            
        df = pd.DataFrame(data, columns=['close'])
        delta = df['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_vwap(self, klines):
        """
        Calculates Volume Weighted Average Price (VWAP).
        klines: list of dicts with 'close', 'high', 'low', 'volume'
        """
        if not klines: return 0.0
        
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_vol'] = df['tp'] * df['volume']
        
        cum_tp_vol = df['tp_vol'].cumsum()
        cum_vol = df['volume'].cumsum()
        
        vwap = cum_tp_vol / cum_vol
        return vwap.iloc[-1]

    def analyze_hft_setup(self, symbol, interval="1m"):
        """
        HFT Scalping Setup (2026 Protocol):
        1. Micro-Trend: EMA 9 vs EMA 21
        2. Momentum: RSI (Fast period 9)
        3. Fair Value: VWAP
        4. Flow: OBI (Order Book Imbalance)
        """
        klines = self.data.get_klines(symbol, interval=interval, limit=100)
        if not klines:
            return {'signal': 'NEUTRAL', 'reason': 'No Data'}
            
        closes = [float(k['close']) for k in klines]
        current_price = closes[-1]
        
        # 1. Trend
        ema_9 = self.calculate_ema(closes, 9)
        ema_21 = self.calculate_ema(closes, 21)
        trend = "BULLISH" if ema_9 > ema_21 else "BEARISH"
        
        # 2. Momentum (RSI Fast)
        rsi = self.calculate_rsi(closes, period=9)
        
        # 3. Value (VWAP)
        vwap = self.calculate_vwap(klines)
        
        # 4. Flow (OBI) - Calculated externally usually, but good to have context
        # We return these values for the Farmer to combine with OBI
        
        setup_score = 0
        signal = "NEUTRAL"
        
        # Logic for HFT
        # Long: Price > VWAP + RSI < 70 (Not Overbought) + Trend Bullish
        # Short: Price < VWAP + RSI > 30 (Not Oversold) + Trend Bearish
        
        if trend == "BULLISH" and current_price > vwap:
            if rsi < 70:
                signal = "HFT_BUY_READY"
            elif rsi > 80:
                signal = "HFT_OVERBOUGHT"
        elif trend == "BEARISH" and current_price < vwap:
            if rsi > 30:
                signal = "HFT_SELL_READY"
            elif rsi < 20:
                signal = "HFT_OVERSOLD"
                
        return {
            'symbol': symbol,
            'price': current_price,
            'vwap': vwap,
            'rsi': rsi,
            'trend': trend,
            'signal': signal
        }

    def analyze_bear_trap(self, symbol, interval="5m"):
        """
        Analyzes if a dip is a Bear Trap using EMAs (9 vs 21).
        Bear Trap Logic:
        - Price dropped recently (Bearish candle)
        - But Price > EMA 21 (Trend is still Bullish/Support holds)
        - Or Price < EMA 9 but recovering
        """
        klines = self.data.get_klines(symbol, interval=interval, limit=50)
        if not klines:
            return {'is_trap': False, 'reason': "No Data"}
            
        closes = [float(k['close']) for k in klines]
        current_price = closes[-1]
        
        ema_9 = self.calculate_ema(closes, 9)
        ema_21 = self.calculate_ema(closes, 21)
        
        # Simple Bear Trap Detection
        # 1. Trend Alignment: EMA 9 > EMA 21 (Bullish Trend Base)
        # 2. Trap Condition: Price dipped below EMA 9 but is above EMA 21 (Support Zone)
        
        is_bullish_trend = ema_9 > ema_21
        is_in_support_zone = (current_price < ema_9) and (current_price > ema_21)
        
        # Extended Trap: Price crossed below EMA 21 briefly but closed above (needs historical check, simplified here)
        
        status = "NEUTRAL"
        if is_bullish_trend:
            if current_price > ema_9:
                status = "BULLISH_MOMENTUM"
            elif is_in_support_zone:
                status = "POTENTIAL_BEAR_TRAP" # Buying opportunity at support
            elif current_price < ema_21:
                status = "BEARISH_BREAKOUT" # Trend might be reversing
        else:
            status = "BEARISH_TREND"
            if current_price > ema_9:
                status = "POTENTIAL_BULL_TRAP" # Selling opportunity at resistance
                
        return {
            'symbol': symbol,
            'current_price': current_price,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'status': status,
            'trend': "BULLISH" if is_bullish_trend else "BEARISH"
        }

    def calculate_dynamic_stop(self, symbol, side, interval="15m"):
        """
        Calculates a 'Smart Stop Loss' based on Moving Averages and Volatility.
        Long: Stop below EMA 21 or VWAP (Support).
        Short: Stop above EMA 21 or VWAP (Resistance).
        """
        klines = self.data.get_klines(symbol, interval=interval, limit=100)
        if not klines: return None
        
        closes = [float(k['close']) for k in klines]
        current_price = closes[-1]
        
        # Calculate Indicators
        ema_21 = self.calculate_ema(closes, 21)
        vwap = self.calculate_vwap(klines)
        
        # ATR-like Buffer (using standard deviation of last 10 candles for simplicity)
        # or just a % buffer. Let's use a % based on recent volatility.
        volatility = np.std(closes[-20:]) if len(closes) >= 20 else current_price * 0.01
        buffer = volatility * 1.5 # 1.5 StdDev buffer
        
        stop_price = 0.0
        reason = ""
        
        if side == "Long":
            # Support is the MAX of (EMA 21, VWAP) usually, but we want the one below price.
            # If Price is above both, use the highest one as support.
            # If Price is between, use the lower one.
            supports = [s for s in [ema_21, vwap] if s < current_price]
            
            if supports:
                primary_support = max(supports)
                stop_price = primary_support - buffer
                reason = f"Below Support ({primary_support:.4f} - Buffer)"
            else:
                # Price is crashing below supports? Use recent low.
                lows = [float(k['low']) for k in klines[-10:]]
                recent_low = min(lows)
                stop_price = recent_low - buffer
                reason = "Below Recent Low"
                
        else: # Short
            # Resistance is MIN of (EMA 21, VWAP) usually, but we want the one above price.
            resistances = [r for r in [ema_21, vwap] if r > current_price]
            
            if resistances:
                primary_resistance = min(resistances)
                stop_price = primary_resistance + buffer
                reason = f"Above Resistance ({primary_resistance:.4f} + Buffer)"
            else:
                # Price is rocketing above resistances? Use recent high.
                highs = [float(k['high']) for k in klines[-10:]]
                recent_high = max(highs)
                stop_price = recent_high + buffer
                reason = "Above Recent High"
                
        return {
            "stop_price": stop_price,
            "ema_21": ema_21,
            "vwap": vwap,
            "reason": reason
        }
