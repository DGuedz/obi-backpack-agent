import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice
from ta.momentum import WilliamsRIndicator

class BackpackIndicators:
    def __init__(self):
        pass

    def calculate_atr(self, df: pd.DataFrame, window=14) -> pd.Series:
        """
        Calcula ATR (Average True Range).
        """
        from ta.volatility import AverageTrueRange
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        atr_ind = AverageTrueRange(high=high, low=low, close=close, window=window)
        return atr_ind.average_true_range()

    def calculate_volume_sma(self, df: pd.DataFrame, window=20) -> pd.Series:
        """
        Calcula Média Móvel de Volume.
        """
        volume = df['volume'].astype(float)
        return volume.rolling(window=window).mean()

    def calculate_rsi(self, df: pd.DataFrame, window=14) -> pd.Series:
        """
        Calcula RSI (Relative Strength Index).
        """
        from ta.momentum import RSIIndicator
        close = df['close'].astype(float)
        rsi_ind = RSIIndicator(close=close, window=window)
        return rsi_ind.rsi()

    def calculate_bollinger_bands(self, df: pd.DataFrame, window=20, window_dev=2) -> dict:
        """
        Calcula Bollinger Bands.
        """
        close = df['close'].astype(float)
        sma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        
        upper = sma + (window_dev * std)
        lower = sma - (window_dev * std)
        
        return {
            "upper": upper,
            "middle": sma,
            "lower": lower
        }

    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula VWAP (Volume Weighted Average Price) Intraday.
        Assumindo que o DF passado já é o recorte desejado.
        """
        close = df['close'].astype(float)
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        volume = df['volume'].astype(float)
        
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        return vwap

    def calculate_ema_cross(self, df: pd.DataFrame, short_window=9, long_window=21) -> dict:
        """
        Calcula EMA Cross (Tendência Rápida).
        """
        close = df['close'].astype(float)
        ema_short = close.ewm(span=short_window, adjust=False).mean()
        ema_long = close.ewm(span=long_window, adjust=False).mean()
        
        return {
            "ema_short": ema_short,
            "ema_long": ema_long,
            "cross_up": (ema_short > ema_long) & (ema_short.shift(1) <= ema_long.shift(1)),
            "cross_down": (ema_short < ema_long) & (ema_short.shift(1) >= ema_long.shift(1))
        }

    def calculate_macd(self, df: pd.DataFrame) -> dict:
        """
        Calcula MACD (Momentum).
        """
        close = df['close'].astype(float)
        macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        
        return {
            "macd": macd.macd(),
            "signal": macd.macd_signal(),
            "hist": macd.macd_diff()
        }

    def calculate_volume_profile(self, df: pd.DataFrame, bins=10) -> dict:
        """
        Calcula Volume Profile simplificado (POC - Point of Control).
        Retorna o nível de preço com maior volume negociado na janela recente.
        """
        close = df['close'].astype(float)
        volume = df['volume'].astype(float)
        
        # Criar histograma de volume por preço
        price_bins = pd.cut(close, bins=bins)
        # Fix FutureWarning: Pass observed=False to retain current behavior
        vol_profile = volume.groupby(price_bins, observed=False).sum()
        
        # Encontrar o intervalo com maior volume (POC)
        poc_interval = vol_profile.idxmax()
        poc_price = poc_interval.mid
        
        return {
            "poc": poc_price,
            "profile": vol_profile
        }

    def calculate_fisher(self, df: pd.DataFrame, length=9) -> tuple[pd.Series, pd.Series]:
        """
        Calcula o Fisher Transform.
        Retorna (Fisher, Trigger).
        """
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        
        price = (high + low) / 2
        min_l = low.rolling(window=length).min()
        max_h = high.rolling(window=length).max()
        
        fisher_series = np.zeros(len(df))
        trigger_series = np.zeros(len(df))
        val1_series = np.zeros(len(df))
        
        prices = price.values
        min_vals = min_l.values
        max_vals = max_h.values
        
        for i in range(1, len(df)):
            if np.isnan(min_vals[i]) or np.isnan(max_vals[i]): continue
                
            div = max_vals[i] - min_vals[i]
            if div == 0: div = 0.000001
                
            val = 0.33 * 2 * ((prices[i] - min_vals[i]) / div - 0.5) + 0.67 * val1_series[i-1]
            if val > 0.99: val = 0.999
            if val < -0.99: val = -0.999
            val1_series[i] = val
            
            fisher = 0.5 * np.log((1 + val) / (1 - val)) + 0.5 * fisher_series[i-1]
            fisher_series[i] = fisher
            trigger_series[i] = fisher_series[i-1]
            
        return pd.Series(fisher_series, index=df.index), pd.Series(trigger_series, index=df.index)

    def calculate_williams_r(self, df: pd.DataFrame, length=14) -> pd.Series:
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        indicator = WilliamsRIndicator(high=high, low=low, close=close, lbp=length)
        return indicator.williams_r()

    def analyze_trend(self, df: pd.DataFrame) -> dict:
        """
        Analisa a tendência usando a 'Santíssima Trindade do Scalp':
        1. EMA Cross (9/21) - Direção
        2. MACD - Força/Momentum
        3. Volume Profile (POC) - Contexto de Suporte/Resistência
        """
        # Calcular Indicadores Base
        df['vwma'] = self.calculate_vwma(df)
        ema_data = self.calculate_ema_cross(df)
        macd_data = self.calculate_macd(df)
        vp_data = self.calculate_volume_profile(df)
        
        # Adicionar ao DataFrame para fácil acesso
        df['ema_short'] = ema_data['ema_short']
        df['ema_long'] = ema_data['ema_long']
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_hist'] = macd_data['hist']
        
        # Análise do Último Candle
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 1. EMA TREND (Direção)
        trend = "NEUTRAL"
        if last['ema_short'] > last['ema_long']:
            trend = "BULLISH"
        elif last['ema_short'] < last['ema_long']:
            trend = "BEARISH"
            
        # 2. MACD MOMENTUM (Força)
        # Histograma positivo e crescente = Aceleração Bullish
        # Histograma negativo e decrescente = Aceleração Bearish
        momentum = "WEAK"
        if last['macd_hist'] > 0 and last['macd_hist'] > prev['macd_hist']:
            momentum = "STRONG_BULL"
        elif last['macd_hist'] < 0 and last['macd_hist'] < prev['macd_hist']:
            momentum = "STRONG_BEAR"
            
        # 3. VOLUME CONTEXT (POC)
        # Preço acima do POC = Suporte (Bullish)
        # Preço abaixo do POC = Resistência (Bearish)
        poc = vp_data['poc']
        price_pos = "ABOVE_POC" if last['close'] > poc else "BELOW_POC"
        
        # --- SINAL FINAL SCALP ---
        signal = "NEUTRAL"
        confidence = 0.0
        
        # Setup LONG: Tendência Bullish + Momentum Bull + Acima do POC
        if trend == "BULLISH" and momentum == "STRONG_BULL" and price_pos == "ABOVE_POC":
            signal = "BUY"
            confidence = 0.9
        elif trend == "BULLISH" and last['macd_hist'] > 0: # Setup secundário (continuação)
            signal = "BUY_HOLD"
            confidence = 0.6
            
        # Setup SHORT: Tendência Bearish + Momentum Bear + Abaixo do POC
        if trend == "BEARISH" and momentum == "STRONG_BEAR" and price_pos == "BELOW_POC":
            signal = "SELL"
            confidence = 0.9
        elif trend == "BEARISH" and last['macd_hist'] < 0:
            signal = "SELL_HOLD"
            confidence = 0.6

        return {
            "signal": signal,
            "confidence": confidence,
            "vwma": last['vwma'],
            "ema_short": last['ema_short'],
            "ema_long": last['ema_long'],
            "macd": last['macd'],
            "poc": poc,
            "close": last['close']
        }
