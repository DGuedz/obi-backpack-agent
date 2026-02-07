import requests
import time

class MacroOracle:
    """
    Agente Macro & Sentimento (The Oracle)
    Missão: Monitorar o 'clima' do mercado para definir o viés (Bias) direcional.
    """
    def __init__(self, data_client=None):
        self.fng_url = "https://api.alternative.me/fng/"
        self.last_check = 0
        self.cache = {}
        self.cache_ttl = 3600 # 1 hour cache for F&G
        self.data = data_client # BackpackData dependency

    def analyze_btc_lighthouse(self):
        """
        Analyzes BTC Technical Trend (4h Timeframe) to act as the Market Lighthouse.
        Returns: BULLISH, BEARISH, NEUTRAL
        """
        if not self.data:
            return "NEUTRAL"
            
        try:
            # Fetch 4h klines (limit 100 to calculate EMA50)
            klines = self.data.get_klines("BTC_USDC", interval="4h", limit=100)
            if not klines:
                return "NEUTRAL"
                
            closes = [float(k['close']) for k in klines]
            volumes = [float(k['volume']) for k in klines]
            import pandas as pd
            import numpy as np
            
            # EMA Calculation
            def ema(series, period):
                return pd.Series(series).ewm(span=period, adjust=False).mean().iloc[-1]
                
            def rsi(series, period=14):
                delta = pd.Series(series).diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs)).iloc[-1]
            
            def volume_ma(series, period=20):
                return pd.Series(series).rolling(window=period).mean().iloc[-1]
            
            # Calculate indicators
            ema20 = ema(closes, 20)
            ema50 = ema(closes, 50)
            ema100 = ema(closes, 100)
            rsi_val = rsi(closes)
            current_volume = volumes[-1]
            volume_ma20 = volume_ma(volumes, 20)
            price = closes[-1]
            
            # Volume analysis
            volume_ratio = current_volume / volume_ma20 if volume_ma20 > 0 else 1
            
            # Momentum analysis
            momentum_1h = ((closes[-1] / closes[-6]) - 1) * 100  # 6 periods = 24h
            
            print(f"    Lighthouse (BTC 4h): Price ${price:,.0f} | EMA20 ${ema20:,.0f} | RSI {rsi_val:.1f}")
            print(f"    Volume: {volume_ratio:.2f}x MA20 | Momentum: {momentum_1h:+.1f}% 24h")
            
            # Enhanced trend analysis with volume confirmation
            if price > ema20 and ema20 > ema50:
                # Bullish trend confirmed by volume
                if rsi_val > 75: 
                    return "NEUTRAL"  # Overbought
                elif volume_ratio > 1.2 and momentum_1h > 2:
                    return "BULLISH_STRONG"
                else:
                    return "BULLISH"
            elif price < ema20 and ema20 < ema50:
                # Bearish trend confirmed by volume
                if rsi_val < 25: 
                    return "NEUTRAL"  # Oversold
                elif volume_ratio > 1.2 and momentum_1h < -2:
                    return "BEARISH_STRONG"
                else:
                    return "BEARISH"
            else:
                # Sideways market - check for breakout conditions
                if volume_ratio > 1.5 and abs(momentum_1h) > 3:
                    if momentum_1h > 0:
                        return "BULLISH_BREAKOUT"
                    else:
                        return "BEARISH_BREAKOUT"
                return "NEUTRAL"
                
        except Exception as e:
            print(f"   ️ Lighthouse Error: {e}")
            return "NEUTRAL"

    def get_macro_report(self):
        """
        Gathers macro data and returns a report with Bias and Restrictions.
        """
        current_time = time.time()
        
        # Always check BTC Trend specifically for "Flash Crashes"
        # This overrides cache if critical
        btc_dump_detected = False
        
        bias = "NEUTRAL"
        restrictions = []
        fng_value = 50 
        
        # 1. Crypto Fear & Greed Index
        if current_time - self.last_check < self.cache_ttl and self.cache:
             # Use cache for F&G but maybe update bias if BTC dumping?
             fng_value = self.cache.get('fng_index', 50)
             bias = self.cache.get('bias', 'NEUTRAL')
             restrictions = self.cache.get('restrictions', [])
        else:
             # Fetch F&G
             try:
                print(" Oracle: Gazing into the Fear & Greed Index...")
                response = requests.get(self.fng_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    fng_value = int(data['data'][0]['value'])
                    if fng_value < 20:
                        restrictions.append("BLOCK_LONG")
                        bias = "BEARISH_EXTREME"
                    elif fng_value > 80:
                        restrictions.append("BLOCK_SHORT")
                        bias = "BULLISH_EXTREME"
                    elif fng_value > 60:
                        bias = "BULLISH"
                    elif fng_value < 40:
                        bias = "BEARISH"
                else:
                    print("   ️ Oracle: Vision clouded. Defaulting to Neutral.")
             except Exception as e:
                print(f"   ️ Oracle Error: {e}")

        # 2. REAL-TIME BTC TREND CHECK (The "Owl Eyes")
        # Since we don't have BackpackData in Oracle directly, we rely on the caller or add simple request?
        # Let's add simple request to Backpack public API for BTC check
        try:
            # Simple public request to check BTC 24h change
            btc_res = requests.get("https://api.backpack.exchange/api/v1/ticker?symbol=BTC_USDC")
            if btc_res.status_code == 200:
                btc_data = btc_res.json()
                change_24h = float(btc_data.get('priceChangePercent', 0))
                price = float(btc_data.get('lastPrice', 0))
                
                print(f"    Oracle Eye on BTC: ${price:,.0f} ({change_24h:+.2f}%)")
                
                if change_24h < -1.0: # Sensitivity Increased to -1%
                    print("   ️ BTC DROP DETECTED (< -1%). SHIFTING BIAS TO BEARISH.")
                    bias = "BEARISH"
                    if "BLOCK_SHORT" in restrictions: restrictions.remove("BLOCK_SHORT")
                    if "BLOCK_LONG" not in restrictions: restrictions.append("BLOCK_LONG")
                elif change_24h < -3.0: # Sensitivity Increased to -3%
                    print("    BTC CRASH ALERT (< -3%). DEFCON 1.")
                    bias = "BEARISH_EXTREME"
                    restrictions = ["BLOCK_LONG"]
        except Exception as e:
            print(f"   ️ Oracle BTC Check Failed: {e}")
            
        report = {
            "agent": "MacroOracle",
            "bias": bias,
            "restrictions": restrictions,
            "fng_index": fng_value,
            "fed_stance": "HAWKISH",
            "timestamp": current_time
        }
        
        self.cache = report
        self.last_check = current_time
        return report
