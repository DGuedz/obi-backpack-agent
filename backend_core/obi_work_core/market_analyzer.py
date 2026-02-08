import pandas as pd

class MarketAnalyzer:
    """
    OBI WORK CORE - Market Analyzer
    Stateless calculation engine.
    """
    
    @staticmethod
    def calculate_rsi(candles: list, period: int = 14) -> float:
        """
        Calculates RSI from Backpack K-Lines.
        Candles format expected: [Timestamp, Open, High, Low, Close, Volume] (Backpack standard)
        Returns the latest RSI value.
        """
        if not candles or len(candles) < period + 1:
            return 50.0 # Neutral default
            
        # Parse into DataFrame
        # Backpack candles: [t, o, h, l, c, v]
        # We only need Close (index 4)
        closes = [float(c['close']) if isinstance(c, dict) else float(c[4]) for c in candles]
        
        series = pd.Series(closes)
        delta = series.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle NaN
        last_rsi = rsi.iloc[-1]
        if pd.isna(last_rsi):
            return 50.0
            
        return float(last_rsi)

if __name__ == "__main__":
    # Mock data
    mock_candles = []
    price = 100.0
    for i in range(50):
        price += (i % 2 == 0) and 1 or -1
        mock_candles.append([0, 0, 0, 0, price, 0])
        
    rsi = MarketAnalyzer.calculate_rsi(mock_candles)
    print(f"Calculated RSI: {rsi}")
