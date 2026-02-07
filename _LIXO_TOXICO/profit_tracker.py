import json
import os
import time

class ProfitTracker:
    def __init__(self, ledger_file="session_ledger.json"):
        self.ledger_file = ledger_file
        self.base_budget = 300.0
        self._load_ledger()
        
    def _load_ledger(self):
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, 'r') as f:
                    data = json.load(f)
                    self.realized_profit = data.get('realized_profit', 0.0)
                    self.base_budget = data.get('base_budget', 300.0)
                    self.daily_trades = data.get('daily_trades', 0)
                    self.last_trade_date = data.get('last_trade_date', "")
            except Exception as e:
                print(f"️ Error loading ledger: {e}")
                self.realized_profit = 0.0
                self.daily_trades = 0
                self.last_trade_date = ""
                self._save_ledger()
        else:
            self.realized_profit = 0.0
            self.daily_trades = 0
            self.last_trade_date = ""
            self._save_ledger()
            
    def _save_ledger(self):
        data = {
            "base_budget": self.base_budget,
            "realized_profit": self.realized_profit,
            "last_update": time.time(),
            "effective_budget": self.base_budget + self.realized_profit,
            "daily_trades": self.daily_trades,
            "last_trade_date": self.last_trade_date
        }
        try:
            with open(self.ledger_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"️ Error saving ledger: {e}")
            
    def increment_trade_count(self):
        """
        Increments daily trade count. Resets if new day.
        """
        today = time.strftime("%Y-%m-%d")
        if self.last_trade_date != today:
            self.daily_trades = 0
            self.last_trade_date = today
            
        self.daily_trades += 1
        self._save_ledger()
        print(f" Daily Trades: {self.daily_trades}")

    def get_trade_count(self):
        today = time.strftime("%Y-%m-%d")
        if self.last_trade_date != today:
            return 0
        return self.daily_trades
            
    def record_profit(self, profit_amount):
        """
        Adds (or subtracts) profit from the ledger.
        profit_amount: float (Positive for gain, Negative for loss)
        """
        self.realized_profit += profit_amount
        self._save_ledger()
        print(f" LEDGER UPDATED: Profit ${profit_amount:+.2f} | Total Profit: ${self.realized_profit:+.2f}")
        print(f" NEW EFFECTIVE BUDGET: ${self.get_effective_budget():.2f}")
        
    def get_effective_budget(self):
        """
        Returns the Base Budget + Realized Profit.
        Used by Bots to determine Capital Limit.
        """
        # Reload to ensure sync across processes
        self._load_ledger()
        return max(self.base_budget + self.realized_profit, 10.0) # Min floor $10

    def reset_ledger(self):
        self.realized_profit = 0.0
        self._save_ledger()
        
    def get_daily_progress(self):
        """
        Returns progress towards $500 daily target (User Request)
        """
        daily_target = 500.0
        progress_percent = (self.realized_profit / daily_target) * 100
        remaining = max(daily_target - self.realized_profit, 0)
        
        return {
            'current_profit': self.realized_profit,
            'daily_target': daily_target,
            'progress_percent': progress_percent,
            'remaining_target': remaining,
            'on_track': self.realized_profit >= 0  # We're on track if not losing money
        }
    
    def print_daily_progress(self):
        """
        Prints beautiful progress bar for $500 daily target
        """
        progress = self.get_daily_progress()
        
        # Progress bar visualization
        bar_length = 20
        filled_length = int(bar_length * progress['progress_percent'] / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f" DAILY TARGET: $500.00 | CURRENT: ${progress['current_profit']:+.2f}")
        print(f" Progress: [{bar}] {progress['progress_percent']:.1f}%")
        print(f" Remaining: ${progress['remaining_target']:.2f} to reach target")
        
        if progress['current_profit'] >= 500:
            print(" CONGRATULATIONS! DAILY TARGET ACHIEVED! ")
        elif progress['current_profit'] < 0:
            print("️  WARNING: Currently at a loss. Zero Loss Policy activated!")
        else:
            trades_needed = progress['remaining_target'] / 50  # Assuming $50 avg profit per trade
            print(f" Estimated trades needed: {trades_needed:.1f} (at $50 avg profit)")
