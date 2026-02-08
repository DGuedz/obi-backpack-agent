from typing import Dict, Any, Optional

class RiskGatekeeper:
    """
    OBI WORK CORE - Risk Gatekeeper
    The final binary gate before execution.
    Vetos any order that violates the immutable session constraints.
    """
    
    def __init__(self, constraints: Dict[str, float]):
        self.constraints = constraints
        self.current_session_loss = 0.0
        
    def check_order(self, 
                    symbol: str, 
                    side: str, 
                    size_usd: float, 
                    leverage: int) -> Tuple[bool, str]:
        """
        Validates an order against constraints.
        Returns (Allowed: bool, Reason: str)
        """
        
        # 1. Check Leverage
        if leverage > self.constraints['max_leverage']:
            return False, f"Leverage {leverage}x exceeds limit {self.constraints['max_leverage']}x"
            
        # 2. Check Size
        if size_usd > self.constraints['max_entry_size_usd']:
            return False, f"Size ${size_usd} exceeds limit ${self.constraints['max_entry_size_usd']:.2f}"
            
        # 3. Check Session Loss (Kill Switch)
        if self.current_session_loss >= self.constraints['hard_stop_loss_usd']:
            return False, f"Session Loss Limit Reached (${self.current_session_loss}). TRADING HALTED."
            
        return True, "Order Approved"

    def update_session_loss(self, realized_pnl: float):
        """Updates the session loss accumulator. Only counts losses."""
        if realized_pnl < 0:
            self.current_session_loss += abs(realized_pnl)

if __name__ == "__main__":
    # Test
    limits = {
        "hard_stop_loss_usd": 50.0,
        "max_leverage": 5,
        "max_entry_size_usd": 200.0,
        "stop_loss_pct": 0.01
    }
    gate = RiskGatekeeper(limits)
    
    # Test 1: Good Order
    allowed, msg = gate.check_order("SOL", "BUY", 100.0, 3)
    print(f"Order 1: {allowed} ({msg})")
    
    # Test 2: Bad Leverage
    allowed, msg = gate.check_order("SOL", "BUY", 100.0, 10)
    print(f"Order 2: {allowed} ({msg})")
    
    # Test 3: Loss Limit
    gate.update_session_loss(-60.0)
    allowed, msg = gate.check_order("SOL", "BUY", 100.0, 3)
    print(f"Order 3: {allowed} ({msg})")
