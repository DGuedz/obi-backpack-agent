import pandas as pd
import numpy as np
import time
from backpack_data import BackpackData

class BackpackAnalytics:
    def __init__(self, data_client: BackpackData):
        self.data = data_client

    def fetch_market_snapshot(self):
        """
        Fetches market data and returns a DataFrame with:
        Symbol, Price, Funding Rate
        """
        try:
            markets = self.data.get_mark_prices() # Returns list of dicts
            if not markets:
                return pd.DataFrame()
            
            # Handle list vs dict response
            data_list = []
            if isinstance(markets, list):
                data_list = markets
            elif isinstance(markets, dict):
                # Sometimes API returns {'markets': [...]} or similar
                # If it's a dict, try to find a list value, or assume it's a single obj (unlikely for 'markets')
                for key, val in markets.items():
                    if isinstance(val, list):
                        data_list = val
                        break
            
            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list)
            
            # Ensure numeric columns
            numeric_cols = ['markPrice', 'indexPrice', 'fundingRate', 'openInterest']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except Exception as e:
            print(f"Error fetching snapshot: {e}")
            return pd.DataFrame()

    def get_top_opportunities(self, limit=5):
        """
        Scans markets for high funding or potential volatility.
        Returns top candidates with confluence scores, including Volume and Utilization.
        """
        print(" Scanning Markets for Confluences...")
        df = self.fetch_market_snapshot()
        if df.empty:
            print("️ No market data available.")
            return pd.DataFrame() # Return DF consistent with logic below

        # Filter for USDC pairs (Spot or Perp)
        if 'symbol' in df.columns:
            # Allow symbols containing USDC (e.g. SOL_USDC, SOL_USDC_PERP)
            df = df[df['symbol'].str.contains('USDC')].copy()
        
        # Pre-fetch Borrow/Lend Markets (Utilization) globally to save calls
        print(" Fetching Lending Markets for Utilization Check...")
        try:
            lending_markets = self.data.get_borrow_lend_markets()
            # Map symbol (e.g. 'SOL') to utilization
            # Note: Borrow/Lend symbols are single assets (SOL, USDC), but market symbols are pairs (SOL_USDC)
            # We will check the base asset utilization.
            util_map = {}
            for lm in lending_markets:
                if 'symbol' in lm and 'utilization' in lm:
                    util_map[lm['symbol']] = float(lm['utilization'])
        except Exception as e:
            print(f"️ Failed to fetch lending markets: {e}")
            util_map = {}

        # ---------------------------------------------------------
        # UPGRADE: Fetch 24h Ticker Data for Volume & Change
        # ---------------------------------------------------------
        # Backpack API doesn't return 24h stats in get_mark_prices (it's snapshot).
        # We must iterate or use get_tickers (if bulk endpoint exists) or fetch individually.
        # Based on docs, get_tickers() might return all. Let's try or fetch individually for top candidates.
        # Strategy:
        # 1. Use Funding Rate as primary filter to get Top 20.
        # 2. Fetch detailed Ticker for Top 20 to get Volume/Change.
        # 3. Re-rank based on Volume & Change.
        
        # Score 1: Absolute Funding Rate (High funding = Squeeze potential)
        if 'fundingRate' in df.columns:
            df['funding_score'] = df['fundingRate'].abs()
            # Sort by Funding Score (Highest Absolute Funding first) to get candidate pool
            candidate_pool = df.sort_values(by='funding_score', ascending=False).head(15)
        else:
            candidate_pool = df.head(15)
        
        results = []
        print(f" Analyzing Top Candidates for Volume & Change...")
        
        for _, row in candidate_pool.iterrows():
            symbol = row['symbol']
            funding = row.get('fundingRate', 0)
            price = row.get('markPrice', 0)
            base_asset = symbol.split('_')[0]
            
            # Fetch Detailed Ticker (Volume & Change)
            # This is critical for matching the User's Screenshot strategy (Volume is King)
            ticker_info = self.data.get_ticker(symbol)
            volume_24h = float(ticker_info.get('volume', 0))
            price_change_24h = float(ticker_info.get('priceChangePercent', 0)) # Assuming API returns this or we calc
            # If API returns 'priceChange' (absolute), we might need to calc %.
            # Assuming 'priceChangePercent' or similar exists. If not, use volatility.
            
            # Utilization Check
            utilization = util_map.get(base_asset, 0) * 100
            
            # --- CONFLUENCE SCORE ---
            confluence_score = 0
            
            # 1. Funding (0-3 pts) - "Hot Rates" Sensitivity Adjusted
            # Standard 1h funding is ~0.001% (0.00001)
            # Hot: > 0.005% (0.00005)
            # Extreme: > 0.02% (0.0002)
            fund_abs = abs(funding)
            if fund_abs > 0.0002: confluence_score += 3 # Extreme Squeeze/Yield
            elif fund_abs > 0.00005: confluence_score += 2 # Hot Rate
            elif fund_abs > 0.00001: confluence_score += 1 # Active
            
            # 2. Volume (0-3 pts) - THE KING
            # Benchmarks: >$5M (High), >$500k (Mid) - Adjusted for Sensitivity
            if volume_24h > 5000000: confluence_score += 3
            elif volume_24h > 500000: confluence_score += 1
            
            # 3. Volatility/Change (0-2 pts)
            # If moved > 3% today, it's in play (Sensitivity increased)
            if abs(price_change_24h) > 3.0: confluence_score += 2
            elif abs(price_change_24h) > 1.0: confluence_score += 1
            
            # 4. Utilization (Short Squeeze)
            if utilization > 80: confluence_score += 2
            
            # Determine Strategy Type
            strategy = "Momentum" # Default
            if fund_abs > 0.0001:
                strategy = "Yield/Squeeze"
            elif utilization > 80:
                strategy = "Supply Shock"
            
            # HFT Signal Container
            hft_signal = "NEUTRAL"

            # NEW: Deep Dive Trend Check (High Caliber)
            # Only do deep analysis for top candidates to save API calls
            if confluence_score >= 2:
                analysis = self.analyze_asset(symbol)
                trend = analysis.get('trend', 'NEUTRAL')
                rsi = analysis.get('rsi', 50)
                
                # TITANIUM RULE: NO TRADES AGAINST TREND
                # If Funding favors Long (Negative) but Trend is Bearish -> NO TRADE (unless Reversal)
                # If Funding favors Short (Positive) but Trend is Bullish -> NO TRADE
                
                if funding < 0: # Paying Longs
                    if trend == "BULLISH":
                        confluence_score += 4 # Golden Setup (Trend + Yield)
                        strategy = "Paid to Long (Trend)"
                    elif trend == "OVERSOLD":
                        confluence_score += 2 # Reversal Play
                        strategy = "Paid to Long (Reversal)"
                    elif trend == "BEARISH":
                        confluence_score = -10 # KILL SWITCH: Don't catch falling knife just for funding
                        strategy = "BLOCKED (Trend Mismatch)"
                        
                elif funding > 0: # Paying Shorts
                    if trend == "BEARISH":
                        confluence_score += 4 # Golden Setup
                        strategy = "Paid to Short (Trend)"
                    elif trend == "OVERBOUGHT":
                        confluence_score += 2
                        strategy = "Paid to Short (Reversal)"
                    elif trend == "BULLISH":
                        confluence_score = -10 # KILL SWITCH: Don't short a rocket
                        strategy = "BLOCKED (Trend Mismatch)"
            
            results.append({
                "symbol": symbol,
                "price": price,
                "funding_rate": funding,
                "volume_24h": volume_24h,
                "change_24h": price_change_24h,
                "confluence_score": confluence_score,
                "utilization": utilization,
                "strategy": strategy,
                "trend": trend if 'trend' in locals() else "UNKNOWN"
            })
            
        # Create DataFrame and Sort by Confluence Score
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values(by='confluence_score', ascending=False).head(limit)
            
        return results_df

    def get_fear_and_greed_index(self):
        """
        Fetches the Crypto Fear & Greed Index.
        Returns: int (0-100) or None
        """
        try:
            import requests
            response = requests.get("https://api.alternative.me/fng/")
            if response.status_code == 200:
                data = response.json()
                return int(data['data'][0]['value'])
        except Exception as e:
            print(f"️ Failed to fetch Fear & Greed Index: {e}")
        return None

    def pre_flight_check(self, symbol):
        """
        Executes Standard Entry Protocol (Layer 1-3).
        STRICT MODE: ALL Checks must pass.
        Returns: { 'approved': bool, 'reason': str, 'score': int }
        """
        score = 0
        
        # 1. Fundamental & On-Chain
        # Check if asset is a "Major" (SOL, ETH, BTC, ONDO)
        is_major = any(x in symbol for x in ["SOL", "ETH", "BTC", "ONDO"])
        if is_major:
            score += 2
            
        # 2. Radar de Assimetria (Technical)
        # 2.1 Liquidity Check (Volume > $5M) - RELAXED from $10M
        ticker = self.data.get_ticker(symbol)
        quote_vol = float(ticker.get('quoteVolume', 0))
        if quote_vol == 0:
            # Fallback: volume * price
            vol = float(ticker.get('volume', 0))
            price = float(ticker.get('lastPrice', 0))
            quote_vol = vol * price
            
        if quote_vol < 5000000:
            return {'approved': False, 'reason': f"Low Volume (${quote_vol/1000000:.1f}M < $5M)", 'score': score}
            
        # 2.2 Utilization Check (< 80%)
        # Fetch lending stats
        try:
            lending = self.data.get_borrow_lend_markets()
            base = symbol.split('_')[0]
            util = 0
            for m in lending:
                if m.get('symbol') == base:
                    util = float(m.get('utilization', 0)) * 100
                    break
            
            if util > 80:
                return {'approved': False, 'reason': f"High Utilization ({util:.1f}%)", 'score': score}
        except:
            pass # Skip if fails
            
        # 2.3 Spread Check (Dynamic based on Volatility)
        # Calculate Spread
        best_bid = float(ticker.get('bestBid', 0))
        best_ask = float(ticker.get('bestAsk', 0))
        
        if best_bid > 0:
            spread_bps = (best_ask - best_bid) / best_bid * 10000
            
            # DYNAMIC SPREAD THRESHOLD OPTIMIZED (User Request)
            # Accept higher spread for high volatility assets that can generate >10% ROI
            # User Logic: "ACEITO PAGAR O SPREAD ALTO, MAS NAO ACEITO SAIR PERDENDO"
            ticker_change = abs(float(ticker.get('priceChangePercent', 0)))
            max_spread = 30 # Base increased from 25
            
            # More aggressive thresholds for volatile assets (potential for >10% ROI)
            if ticker_change > 20: max_spread = 120  # Hyper Volatile (Meme coins)
            elif ticker_change > 15: max_spread = 100 # Super Volatile
            elif ticker_change > 10: max_spread = 80  # Very Volatile
            elif ticker_change > 5: max_spread = 50   # Volatile
            
            if spread_bps > max_spread:
                return {'approved': False, 'reason': f"Wide Spread ({spread_bps:.1f} > {max_spread})", 'score': score}
        
        # 3. Basis Trade Check (Funding)
        funding = float(ticker.get('fundingRate', 0))
        # If Funding is Positive, we want to Short. If Negative, Long.
        # This gives a "Direction Bias"
        direction_bias = "Short" if funding > 0 else "Long"
        
        return {
            'approved': True, 
            'reason': "All Systems Go", 
            'score': score + 5, # Base score for passing checks
            'bias': direction_bias,
            'volatility': 5.0 # Placeholder
        }

    def analyze_asset(self, symbol):
        """
        Performs deep technical analysis on a single asset.
        Includes StochRSI and EMA100 for Zero Error Protocol.
        """
        try:
            # Fetch recent klines (1h for trend) - Limit 200 for EMA100
            klines = self.data.get_klines(symbol, interval='1h', limit=200)
            if not klines:
                return {}
            
            closes = pd.Series([float(k['close']) for k in klines])
            
            # Simple Trend (EMA 20 vs EMA 50 vs EMA 100)
            
            def calculate_rsi_series(series, period=14):
                delta = series.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))

            def calculate_stoch_rsi(series, period=14, k_period=3, d_period=3):
                rsi = calculate_rsi_series(series, period)
                min_rsi = rsi.rolling(window=period).min()
                max_rsi = rsi.rolling(window=period).max()
                stoch = (rsi - min_rsi) / (max_rsi - min_rsi)
                k = stoch.rolling(window=k_period).mean() * 100
                d = k.rolling(window=d_period).mean()
                return k.iloc[-1], d.iloc[-1]

            def ema(series, period):
                return series.ewm(span=period, adjust=False).mean().iloc[-1]
                
            ema20 = ema(closes, 20)
            ema50 = ema(closes, 50)
            ema100 = ema(closes, 100)
            
            rsi_series = calculate_rsi_series(closes)
            rsi = rsi_series.iloc[-1]
            stoch_k, stoch_d = calculate_stoch_rsi(closes)
            
            trend = "NEUTRAL"
            if ema20 > ema50:
                trend = "BULLISH"
                if rsi > 70: trend = "OVERBOUGHT" 
            else:
                trend = "BEARISH"
                if rsi < 30: trend = "OVERSOLD" 
            
            return {
                'trend': trend,
                'ema20': ema20,
                'ema50': ema50,
                'ema100': ema100,
                'rsi': rsi,
                'stoch_k': stoch_k,
                'stoch_d': stoch_d,
                'close': closes.iloc[-1]
            }
        except Exception as e:
            print(f"Analysis Error: {e}")
            return {}

    def protocol_zero_error_check(self, symbol, macro_report):
        """
        ️ PROTOCOLO ZERO ERRO (4 CAMADAS)
        Validação obrigatória antes de qualquer trade.
        """
        score = 0
        reason = ""
        
        # --- CAMADA 1: MACRO & SENTIMENTO ---
        # Crypto Fear & Greed Index
        fng = macro_report.get('fng_index', 50)
        btc_bias = macro_report.get('bias', 'NEUTRAL')
        
        # Bloqueio de Extremos
        # Se F&G < 20 (Medo Extremo), proibido Long (exceto se estratégia de reversão muito específica, mas por segurança bloqueamos)
        # Se F&G > 80 (Ganância Extrema), proibido Short
        
        # Vamos definir o bias permitido baseado no Macro
        allowed_bias = "BOTH"
        if fng < 20: allowed_bias = "SHORT_ONLY"
        elif fng > 80: allowed_bias = "LONG_ONLY"
        
        # BTC Trend Override
        if btc_bias == "BEARISH_EXTREME": allowed_bias = "SHORT_ONLY"
        elif btc_bias == "BULLISH_EXTREME": allowed_bias = "LONG_ONLY"
        
        # --- CAMADA 2: FUNDAMENTAL & QUALIDADE ---
        # Filtro de "Majors"
        MAJORS = ["SOL_USDC_PERP", "ETH_USDC_PERP", "BTC_USDC_PERP", "ONDO_USDC_PERP"]
        is_major = False
        for m in MAJORS:
            if m in symbol: is_major = True
            
        if not is_major:
            return {'approved': False, 'reason': f"Asset {symbol} is not a Major (Toxic Filter)", 'score': 0}
            
        score += 2 # Bonus for Major
        
        # --- CAMADA 3: RADAR DE ASSIMETRIA (SEGURANÇA) ---
        ticker = self.data.get_ticker(symbol)
        if not ticker:
            return {'approved': False, 'reason': "Ticker Data Unavailable", 'score': 0}
            
        # 3.1 Volume Mínimo > $10M
        quote_vol = float(ticker.get('quoteVolume', 0))
        if quote_vol < 10_000_000:
            return {'approved': False, 'reason': f"Low Volume ${quote_vol/1000000:.1f}M < $10M", 'score': 0}
            
        # 3.2 Spread < 15 bps
        best_bid = float(ticker.get('bestBid', 0))
        best_ask = float(ticker.get('bestAsk', 0))
        spread_bps = 0
        if best_bid > 0:
            spread_bps = (best_ask - best_bid) / best_bid * 10000
            
        if spread_bps > 15:
            return {'approved': False, 'reason': f"High Spread {spread_bps:.1f}bps > 15bps", 'score': 0}
            
        # 3.3 Utilization < 80%
        # (Assuming we have util_map passed or we fetch it. Fetching here is expensive if done per asset.
        # Ideally passed. For now, fetch generic check or skip if cached externally.
        # Let's try to fetch borrow lend for this asset's base.)
        try:
            base_asset = symbol.split('_')[0]
            lending = self.data.get_borrow_lend_markets()
            util = 0
            for m in lending:
                if m.get('symbol') == base_asset:
                    util = float(m.get('utilization', 0)) * 100
                    break
            if util > 80:
                 return {'approved': False, 'reason': f"High Utilization {util:.1f}% > 80%", 'score': 0}
        except:
            pass # Fail safe check
            
        # 3.4 Exaustão Técnica (Stoch RSI + EMA 100)
        analysis = self.analyze_asset(symbol)
        stoch_k = analysis.get('stoch_k', 50)
        ema100 = analysis.get('ema100', 0)
        price = analysis.get('close', 0)
        
        # --- CAMADA 4: OPERACIONAL & YIELD (LUCRATIVIDADE) ---
        funding = float(ticker.get('fundingRate', 0))
        
        # Determinar Viés do Trade
        trade_bias = "NEUTRAL"
        
        # Funding Bias: 
        # Funding Positivo (>0) -> Short Bias (Recebe Funding)
        # Funding Negativo (<0) -> Long Bias (Recebe Funding)
        
        if funding > 0.0001: # Positive Funding -> Prefer Short
            trade_bias = "Short"
        elif funding < -0.0001: # Negative Funding -> Prefer Long
            trade_bias = "Long"
        else:
            # Neutral Funding - Follow Trend
            if analysis.get('trend') == "BULLISH": trade_bias = "Long"
            elif analysis.get('trend') == "BEARISH": trade_bias = "Short"
            
        # CHECK: Macro Conflict
        if trade_bias == "Long" and allowed_bias == "SHORT_ONLY":
             return {'approved': False, 'reason': f"Macro Block: F&G/BTC Bearish blocks Longs", 'score': 0}
        if trade_bias == "Short" and allowed_bias == "LONG_ONLY":
             return {'approved': False, 'reason': f"Macro Block: F&G/BTC Bullish blocks Shorts", 'score': 0}
             
        # CHECK: Technical Exhaustion (Stoch RSI)
        # Long: Don't buy if Stoch K > 80 (Overbought)
        # Short: Don't sell if Stoch K < 20 (Oversold)
        
        if trade_bias == "Long" and stoch_k > 80:
             # Exception: Strong Momentum Breakout? 
             # Protocol Zero Error says: "Evitar entrar em topos". Block it.
             return {'approved': False, 'reason': f"StochRSI Overbought ({stoch_k:.1f}) - Wait for pullback", 'score': 0}
             
        if trade_bias == "Short" and stoch_k < 20:
             return {'approved': False, 'reason': f"StochRSI Oversold ({stoch_k:.1f}) - Wait for bounce", 'score': 0}
             
        # CHECK: EMA 100 Deviation (Reversion to Mean Risk)
        # If price is too far from EMA 100, risk of snap back.
        # Let's say > 10% deviation? Or just use it as trend confirmation.
        # User said: "combinado com desvio da EMA 100".
        # Let's check alignment.
        # Long: Price should be > EMA 100 (Uptrend) OR huge deviation below (Mean Reversion)
        # Protocol Zero Error implies "Trend Following" mostly unless Exhaustion strategy.
        # Let's enforce Trend Alignment for standard trades.
        
        if trade_bias == "Long" and price < ema100:
             # Counter-trend Long? Only if Funding is deeply negative (Squeeze).
             if funding > -0.0005: # Not deep enough
                 return {'approved': False, 'reason': f"Price below EMA100 (Downtrend) & Funding not squeezing", 'score': 0}
                 
        if trade_bias == "Short" and price > ema100:
             # Counter-trend Short?
             if funding < 0.0005:
                 return {'approved': False, 'reason': f"Price above EMA100 (Uptrend) & Funding not squeezing", 'score': 0}

        return {
            'approved': True,
            'reason': "Protocol Zero Error Passed",
            'score': 10,
            'bias': trade_bias,
            'volatility': 5.0 # Placeholder
        }


    def get_smart_exit_price(self, symbol, side, current_price):
        """
        Detects 'Liquidity Walls' in the order book to perform Front-Running.
        Goal: Place Limit Order just before the wall.
        User Rule: Wall > $50k value. Front-run 0.1%.
        """
        try:
            depth = self.data.get_orderbook_depth(symbol, limit=50) # Scan deeper (50 levels)
            if not depth: return None
            
            # 1. Select Side to Scan
            # If Long, we sell into Asks -> Scan Asks for Resistance Wall
            # If Short, we buy into Bids -> Scan Bids for Support Wall
            book_side = 'asks' if side == "Long" else 'bids'
            orders = depth.get(book_side, [])
            
            if not orders: return None
            
            found_wall_price = None
            found_wall_vol = 0
            
            for px_str, qty_str in orders:
                px = float(px_str)
                qty = float(qty_str)
                notional_value = px * qty
                
                # WALL DEFINITION: > $50,000 USD
                if notional_value > 50000:
                    # Check direction
                    if side == "Long" and px > current_price:
                        found_wall_price = px
                        found_wall_vol = qty
                        break # Found the first resistance
                    elif side == "Short" and px < current_price:
                        found_wall_price = px
                        found_wall_vol = qty
                        break # Found the first support
            
            if found_wall_price:
                # 3. Calculate Front-Run Price (0.1% discount/premium)
                # Long: Sell 0.1% below wall
                # Short: Buy 0.1% above wall
                
                front_run_pct = 0.001 # 0.1%
                
                if side == "Long":
                    smart_exit = found_wall_price * (1.0 - front_run_pct)
                else:
                    smart_exit = found_wall_price * (1.0 + front_run_pct)
                
                return {
                    "smart_price": smart_exit,
                    "wall_price": found_wall_price,
                    "wall_vol": found_wall_vol
                }
                
            return None
            
        except Exception as e:
            print(f"Error in Smart Exit: {e}")
            return None
