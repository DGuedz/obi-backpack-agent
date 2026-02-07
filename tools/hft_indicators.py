
import math
import pandas as pd
import numpy as np

class HFTIndicators:
    """
     HFT INDICATORS MODULE
    Focado em baixa latência e captura de micro-tendências.
    """
    
    def __init__(self):
        pass

    def calculate_vwap(self, klines):
        """
        Calcula o VWAP (Volume Weighted Average Price) Intraday.
        VWAP = Sum(Price * Volume) / Sum(Volume)
        """
        if not klines: return 0.0
        
        # Klines format: { 'open': '...', 'high': '...', 'low': '...', 'close': '...', 'volume': '...' }
        # or list of dicts. Assuming list of dicts or objects.
        
        cum_pv = 0.0
        cum_vol = 0.0
        
        for k in klines:
            try:
                # Typical Price = (High + Low + Close) / 3
                high = float(k.get('high', 0))
                low = float(k.get('low', 0))
                close = float(k.get('close', 0))
                vol = float(k.get('volume', 0))
                
                tp = (high + low + close) / 3
                
                cum_pv += (tp * vol)
                cum_vol += vol
            except:
                continue
                
        if cum_vol == 0: return 0.0
        
        return cum_pv / cum_vol

    def calculate_ema(self, prices, period=9):
        """
        Calcula EMA (Exponential Moving Average) otimizada.
        """
        if not prices or len(prices) < period: return 0.0
        
        # Simple implementation for speed (or use numpy)
        alpha = 2 / (period + 1)
        ema = prices[0] # Initialize with SMA or first item
        
        # Calculate SMA for first period? Or just iterate.
        # Standard: SMA first, then EMA.
        # Fast approximation: Iterate all.
        
        for p in prices:
            ema = (p * alpha) + (ema * (1 - alpha))
            
        return ema

    def calculate_rsi(self, prices, period=14):
        """
        Calcula RSI (Relative Strength Index).
        """
        if not prices or len(prices) < period + 1: return 50.0
        
        gains = 0.0
        losses = 0.0
        
        # First period
        for i in range(1, period + 1):
            change = prices[i] - prices[i-1]
            if change > 0: gains += change
            else: losses += abs(change)
            
        avg_gain = gains / period
        avg_loss = losses / period
        
        # Smoothing
        for i in range(period + 1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                avg_gain = (avg_gain * (period - 1) + change) / period
                avg_loss = (avg_loss * (period - 1) + 0) / period
            else:
                avg_gain = (avg_gain * (period - 1) + 0) / period
                avg_loss = (avg_loss * (period - 1) + abs(change)) / period
                
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """
        Calcula Bollinger Bands (Upper, Middle, Lower).
        Retorna (upper, middle, lower).
        """
        if not prices or len(prices) < period: return 0.0, 0.0, 0.0
        
        # Simple Moving Average (Middle Band)
        # Using the last 'period' prices
        recent_prices = prices[-period:]
        middle_band = sum(recent_prices) / period
        
        # Standard Deviation
        variance = sum([((x - middle_band) ** 2) for x in recent_prices]) / period
        std = math.sqrt(variance)
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band

class LeakyBucket:
    """
     LEAKY BUCKET (Order Flow Exhaustion)
    Simula o esgotamento de fluxo.
    """
    def __init__(self, capacity=100.0, leak_rate=10.0):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.level = 0.0
        self.last_update = 0
        
    def update(self, volume_in, current_time):
        # Leak first
        if self.last_update > 0:
            elapsed = current_time - self.last_update
            leak_amount = self.leak_rate * elapsed
            self.level = max(0.0, self.level - leak_amount)
            
        # Fill
        self.level += volume_in
        self.last_update = current_time
        
        # Check Overflow (Exhaustion/Saturation)
        is_overflow = False
        if self.level > self.capacity:
            is_overflow = True
            # Don't cap level immediately to allow sustained pressure detection?
            # Or cap it? Let's cap to show "full saturation".
            self.level = self.capacity 
            
        saturation_pct = self.level / self.capacity
        return saturation_pct, is_overflow
