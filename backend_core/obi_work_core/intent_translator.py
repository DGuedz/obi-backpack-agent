from typing import Dict, Any, List

class StrategyConfig:
    """Data Class for Strategy Parameters"""
    def __init__(self, 
                 rsi_buy: int, 
                 rsi_sell: int, 
                 order_type: str, 
                 timeframe: str,
                 use_trailing_stop: bool):
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell
        self.order_type = order_type
        self.timeframe = timeframe
        self.use_trailing_stop = use_trailing_stop

    def __repr__(self):
        return f"StrategyConfig(RSI Buy<{self.rsi_buy}, Sell>{self.rsi_sell}, Type={self.order_type})"

class IntentTranslator:
    """
    OBI WORK CORE - Intent Translator
    Translates Human Intent (VSC Risk Profile) into Machine Logic (Strategy Config).
    """
    
    def __init__(self, context: Dict[str, Any]):
        self.profile = context.get('risk_profile', 'defensive')
        self.assets = context.get('assets', [])
        
    def translate(self) -> StrategyConfig:
        """Derives technical parameters from the abstract risk profile."""
        
        if self.profile == "aggressive":
            return StrategyConfig(
                rsi_buy=35,       # Higher tolerance
                rsi_sell=65,
                order_type="Market", # Speed priority
                timeframe="1m",
                use_trailing_stop=False # Take profit quickly
            )
            
        elif self.profile == "defensive":
            return StrategyConfig(
                rsi_buy=25,       # Strict entry
                rsi_sell=75,
                order_type="Limit", # Fee priority
                timeframe="5m",
                use_trailing_stop=True # Protect gains
            )
            
        elif self.profile == "strategic_conservative":
            return StrategyConfig(
                rsi_buy=20,       # Very strict
                rsi_sell=80,
                order_type="Limit", # Maker only (PostOnly handled in client?)
                timeframe="15m",
                use_trailing_stop=True
            )
            
        else:
            # Default fallback
            return StrategyConfig(
                rsi_buy=30,
                rsi_sell=70,
                order_type="Limit",
                timeframe="5m",
                use_trailing_stop=True
            )

if __name__ == "__main__":
    # Test
    ctx = {"risk_profile": "aggressive", "assets": ["SOL"]}
    translator = IntentTranslator(ctx)
    config = translator.translate()
    print(f"Intent: {ctx['risk_profile']}")
    print(f"Translated Logic: {config}")
