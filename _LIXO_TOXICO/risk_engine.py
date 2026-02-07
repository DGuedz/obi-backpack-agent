import pandas as pd

class RiskEngine:
    """
    Advanced Risk Engine for Dynamic Leverage and Position Sizing.
    Determines leverage based on 'Asymmetry Potential' (Score vs Volatility).
    """
    
    def __init__(self):
        pass
        
    def calculate_dynamic_leverage(self, symbol, confluence_score, volatility_24h, funding_rate):
        """
        Calculates optimal leverage (5x - 50x) based on risk factors.
        
        Args:
            symbol (str): Asset symbol
            confluence_score (float): 0-15 Score from Analytics
            volatility_24h (float): 24h Volatility percentage (e.g. 5.0 for 5%)
            funding_rate (float): Hourly funding rate
            
        Returns:
            int: Leverage (5, 10, 20, 40, 50)
        """
        
        # Strict Safety Mode ($300 Capital)
        # UPDATED: Basis Trade Mode ($300) -> 5x Leverage Fixed (User Rule: Teto fixo de 5x)
        
        leverage = 5 # Default and Max
        
        # Override removed for Fortress Protocol v4.0
        # if confluence_score >= 8: # Super High Score
        #    leverage = 10
            
        # Volatility Penalty
        if volatility_24h > 10.0:
            leverage = 2 # Extreme safety for volatile assets
            
        # Cap for Alts
        is_major = any(x in symbol for x in ["BTC", "ETH", "SOL", "PAXG", "ONDO"])
        if not is_major:
             leverage = 3
             
        return int(leverage)

    def calculate_position_size_usd(self, capital_available, leverage, volatility_24h, risk_per_trade_usd=None):
        """
        Calculates position size (Margin) to risk only 1.9% of capital on Stop Loss.
        Formula: Notional = Risk_USD / Stop_Loss_Pct
        Margin = Notional / Leverage
        
        NEW IRON RULE (Recovery Mode $300): 
        - Stop Loss Distance: 1.9% (0.019) -> Adjusted to 1.5% Hard Stop
        - Risk per Trade: 1.5% of Capital (Conservative)
        - Min Size: $50 USD (User Request)
        """
        # Fixed Risk Parameters
        stop_loss_pct = 0.015 # 1.5% Distance
        
        # Calculate Risk Amount ($)
        if risk_per_trade_usd is None:
            risk_per_trade_usd = capital_available * 0.015
            
        # 2. Calculate Max Notional Size allowed
        max_notional = risk_per_trade_usd / stop_loss_pct
        
        # 3. Calculate Margin needed
        required_margin = max_notional / leverage
        
        # 4. Enforce Minimum Size ($50)
        # User Request: "Mão mínima de $50 USD"
        if required_margin < 50.0:
            required_margin = 50.0
        
        # 5. Cap at Available Capital
        if required_margin > capital_available:
            required_margin = capital_available
            
        return required_margin, stop_loss_pct
