from typing import Dict, Any, Tuple

class RiskDesignEngine:
    """
    OBI WORK CORE - Risk Design Engine
    Transforms declared risk profile into mathematical execution limits.
    """
    
    PROFILES = {
        "aggressive": {
            "max_drawdown_session": 0.10, # 10%
            "leverage_cap": 20,
            "stop_loss_default": 0.02, # 2%
            "entry_size_pct": 0.20 # 20% of balance
        },
        "defensive": {
            "max_drawdown_session": 0.03, # 3%
            "leverage_cap": 5,
            "stop_loss_default": 0.01, # 1%
            "entry_size_pct": 0.05 # 5% of balance
        },
        "strategic_conservative": {
            "max_drawdown_session": 0.01, # 1%
            "leverage_cap": 1, # Spot only
            "stop_loss_default": 0.005, # 0.5%
            "entry_size_pct": 0.10
        }
    }
    
    def __init__(self, context: Dict[str, Any]):
        self.profile_name = context.get('risk_profile', 'defensive')
        self.declared_max_loss = context.get('max_loss_usd', 0.0)
        self.declared_max_entry = context.get('max_entry_size', 0.0)
        
        if self.profile_name not in self.PROFILES:
            raise ValueError(f"Invalid Risk Profile: {self.profile_name}")
            
        self.params = self.PROFILES[self.profile_name]
        
    def generate_constraints(self, current_balance: float) -> Dict[str, float]:
        """
        Calculates hard limits based on balance and profile.
        Returns a dict of immutable constraints for the session.
        """
        
        # 1. Calculate Max Loss Limit (Lower of Declared vs Profile %)
        profile_loss_limit = current_balance * self.params['max_drawdown_session']
        
        # If declared max loss is non-zero, take the tighter constraint
        if self.declared_max_loss > 0:
            hard_loss_limit = min(profile_loss_limit, self.declared_max_loss)
        else:
            hard_loss_limit = profile_loss_limit

        # 2. Calculate Max Entry Size
        profile_entry_size = current_balance * self.params['entry_size_pct']
        if self.declared_max_entry > 0:
            max_entry = min(profile_entry_size, self.declared_max_entry)
        else:
            max_entry = profile_entry_size
            
        constraints = {
            "hard_stop_loss_usd": hard_loss_limit,
            "max_leverage": self.params['leverage_cap'],
            "max_entry_size_usd": max_entry,
            "stop_loss_pct": self.params['stop_loss_default']
        }
        
        return constraints

if __name__ == "__main__":
    # Test
    ctx = {"risk_profile": "defensive", "max_loss_usd": 50.0}
    engine = RiskDesignEngine(ctx)
    limits = engine.generate_constraints(current_balance=1000.0)
    print(f"Risk Profile: {ctx['risk_profile']}")
    print("Generated Constraints:")
    for k, v in limits.items():
        print(f"  {k}: {v}")
