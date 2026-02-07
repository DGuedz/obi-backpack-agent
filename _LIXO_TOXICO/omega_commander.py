import time
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Import Real Modules
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators
from technical_oracle import MarketProxyOracle
from btc_sniper import sniper_entry # Functional approach
from weaver_grid import WeaverGrid # Class approach

# --- CONFIG ---
SYMBOL = "BTC_USDC_PERP"

class AgentBase:
    def __init__(self, name, role, icon):
        self.name = name
        self.role = role
        self.icon = icon
        self.status = "ONLINE"

    def introduce(self):
        return f"{self.icon} **{self.name}** | {self.role} | Status: {self.status}"
        
    def execute_task(self, task, *args):
        return f"️ {self.name} does not support task: {task}"

class OrchestratorAgent(AgentBase):
    def __init__(self, data_engine, indicators):
        super().__init__("Orchestrator", "Cérebro Central & Gestão de Volatilidade", "")
        self.data = data_engine
        self.indicators = indicators
        self.atr_threshold = 500.00
        
    def get_live_data(self):
        try:
            candles = self.data.get_klines(SYMBOL, "1h", limit=20)
            if candles:
                df = pd.DataFrame(candles)
                df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
                df['close'] = df['close'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                atr = self.indicators.calculate_atr(df, window=14).iloc[-1]
                return atr
        except:
            return 0.0
        return 0.0

    def report(self):
        atr_value = self.get_live_data()
        mode = "WEAVER_GRID" if atr_value < self.atr_threshold else "SMART_ENTRY_SNIPER"
        return f"""
        {self.introduce()}
         **Análise Macro:**
        - Volatilidade (ATR): {atr_value:.2f} (Limiar: {self.atr_threshold})
        - Decisão Tática: {'Mercado Lateral' if atr_value < self.atr_threshold else 'Alta Volatilidade'}
        - Comando Ativo: **{mode}**
        """

class OracleAgent(AgentBase):
    def __init__(self, oracle_engine):
        super().__init__("Technical Oracle", "Juiz de Confluência & OBI", "")
        self.oracle = oracle_engine
    
    def report(self):
        obi = self.oracle.get_order_book_imbalance()
        bias, funding = self.oracle.get_funding_bias()
        walls_status = "Clean"
        if obi > 0.3: walls_status = "Bid Wall (Support)"
        elif obi < -0.3: walls_status = "Ask Wall (Resistance)"
        return f"""
        {self.introduce()}
        ️ **Veredito On-Chain Proxy:**
        - OBI: {obi:.4f} ({'Compra' if obi > 0 else 'Venda'})
        - Funding Bias: {bias} ({funding*100:.4f}%)
        - Paredes: {walls_status}
        """

class SentinelAgent(AgentBase):
    def __init__(self, data_engine, trade_engine):
        super().__init__("Sentinel", "Escudo de Capital & Kill-Switch", "️")
        self.data = data_engine
        self.trade = trade_engine
        
    def get_live_stats(self):
        try:
            collateral = self.data.get_account_collateral()
            margin_fraction = collateral.get('marginFraction', 'N/A')
            positions = self.data.get_positions()
            total_pnl = sum([float(p.get('unrealizedPnl', 0)) for p in positions])
            return margin_fraction, total_pnl, len(positions)
        except:
            return "N/A", 0.0, 0

    def report(self):
        mf, pnl, pos_count = self.get_live_stats()
        return f"""
        {self.introduce()}
         **Status de Blindagem:**
        - Margin Fraction: {mf}
        - PnL Sessão: ${pnl:.2f}
        - Posições: {pos_count}
        """
    
    def execute_task(self, task, *args):
        if task == "panic":
            print("️ [SENTINEL] EXECUTING PANIC CLOSE ALL...")
            positions = self.data.get_positions()
            for pos in positions:
                symbol = pos.get('symbol')
                qty = float(pos.get('netQuantity'))
                side = "Ask" if qty > 0 else "Bid"
                abs_qty = abs(qty)
                print(f"   Closing {symbol} ({qty})...")
                self.trade.execute_order(symbol, side, 0, abs_qty, order_type="Market", reduce_only=True)
            return " PANIC CLOSE EXECUTED."
            
        elif task == "audit":
            print("️ [SENTINEL] DEEP SCAN - POSITION AUDIT...")
            positions = self.data.get_positions()
            if not positions:
                return " No open positions. Margin is FREE."
                
            report = "\n    OPEN POSITIONS:\n"
            for pos in positions:
                symbol = pos.get('symbol')
                qty = float(pos.get('netQuantity'))
                entry = float(pos.get('entryPrice', 0))
                mark = float(pos.get('markPrice', 0))
                pnl = float(pos.get('unrealizedPnl') or 0) # Handle None safely
                initial_margin = float(pos.get('initialMargin', 0))
                leverage = float(pos.get('leverage', 10))
                
                report += f"    {symbol}: {qty} @ ${entry:.2f} (Mark: ${mark:.2f})\n"
                report += f"      PnL: ${pnl:.2f} | Margin Used: ${initial_margin:.2f} ({leverage}x)\n"
                
            collateral = self.data.get_account_collateral()
            avail_bal = collateral.get('availableToTrade', 'N/A')
            report += f"\n    Available Balance: ${avail_bal}"
            return report
             
        elif task == "clean":
            print("️ [SENTINEL] CLEANING ORDER BOOK (Cancel All)...")
            # Fallback manual loop directly as cancel_all might not be standard
            try:
                # Assuming data_engine has get_open_orders
                open_orders = self.data.get_open_orders(SYMBOL)
                if not open_orders:
                    return " No open orders to clean."
                for order in open_orders:
                    oid = order.get('id')
                    print(f"   Cancelling {oid}...")
                    self.trade.cancel_order(SYMBOL, oid)
                return " All orders cancelled. Margin freed."
            except Exception as e:
                return f"️ Clean error: {e}"
            
        return super().execute_task(task, *args)

class WeaverAgent(AgentBase):
    def __init__(self, orchestrator_ref, data, trade, indicators):
        super().__init__("Weaver Grid", "Motor de Renda Passiva (Maker)", "️")
        self.orch = orchestrator_ref
        self.engine = WeaverGrid(SYMBOL, data, trade, indicators)
    
    def report(self):
        atr = self.orch.get_live_data()
        spacing = atr * 0.5
        return f"""
        {self.introduce()}
        ️ **Tecelagem de Ordens:**
        - Espaçamento Dinâmico: ${spacing:.2f}
        - Alvo: {SYMBOL}
        """
        
    def execute_task(self, task, *args):
        if task == "weave":
            print("️ [WEAVER] Manually Triggering Grid Layer...")
            self.engine.execute_grid()
            return " Grid Layer Placed."
            
        elif task == "expand":
            print("️ [WEAVER] Expanding Grid (Outer Layer)...")
            # Calculate Outer Layer (2x Spacing)
            self.engine.execute_grid(spacing_multiplier=2.0)
            return " Grid Expanded (Outer Layer Placed)."
            
        return super().execute_task(task, *args)

class SniperAgent(AgentBase):
    def __init__(self):
        super().__init__("Smart Entry Sniper", "Operador de Tendência (Aegis)", "")
    
    def report(self):
        return f"""
        {self.introduce()}
         **Mira Tática:**
        - Protocolo Aegis: ATIVO
        - Status: ESPERA
        """
        
    def execute_task(self, task, *args):
        if task == "attack":
            print(" [SNIPER] Manually Triggering Attack Sequence...")
            # Import dynamically to avoid circle or just call logic
            # Assuming btc_sniper.sniper_entry is self-contained or we use SmartEntrySniper logic
            # Using btc_sniper module directly as it's cleaner for 'attack'
            try:
                sniper_entry()
                return " Sniper Sequence Completed."
            except Exception as e:
                return f" Sniper Failed: {e}"
        return super().execute_task(task, *args)

class AccountingAgent(AgentBase):
    def __init__(self, data_engine):
        super().__init__("Accounting", "Auditoria de Volume", "")
        self.data = data_engine

    def report(self):
        return f"""
        {self.introduce()}
        - Ready to audit volume.
        """
        
    def execute_task(self, task, *args):
        if task == "audit":
            print(" [ACCOUNTING] Running 7-Day Volume Audit...")
            os.system("python3 check_volume.py")
            return " Audit Completed."
            
        elif task == "orders":
            print(" [ACCOUNTING] Scanning Open Orders...")
            orders = self.data.get_open_orders(SYMBOL)
            if not orders:
                return " No open orders found."
            
            report = "\n    OPEN ORDERS (Locked Margin):\n"
            total_locked = 0.0
            
            for o in orders:
                oid = o.get('id')
                side = o.get('side')
                price = float(o.get('price'))
                qty = float(o.get('quantity'))
                order_type = o.get('orderType')
                
                # Estimate Margin Locked (10x Leverage)
                notional = price * qty
                margin = notional / 10.0
                total_locked += margin
                
                report += f"    {side} {qty} @ ${price:.2f} ({order_type})\n"
                report += f"      Notional: ${notional:.2f} | Est. Margin: ${margin:.2f}\n"
                
            report += f"\n    Total Estimated Margin Locked: ${total_locked:.2f}"
            return report
            
        return super().execute_task(task, *args)

# --- COMMANDER DISPATCHER ---
def dispatch(agent_name, action=None):
    # Init Connections
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    indicators = BackpackIndicators()
    oracle_engine = MarketProxyOracle(SYMBOL, auth, data)
    
    # Init Agents
    orch = OrchestratorAgent(data, indicators)
    oracle = OracleAgent(oracle_engine)
    sentinel = SentinelAgent(data, trade)
    weaver = WeaverAgent(orch, data, trade, indicators)
    sniper = SniperAgent()
    accounting = AccountingAgent(data)
    
    agents = {
        "brain": orch,
        "oracle": oracle,
        "shield": sentinel,
        "weaver": weaver,
        "sniper": sniper,
        "accounting": accounting
    }
    
    print("\n--- ️ OMEGA COMMANDER DISPATCH ---")
    
    if agent_name == "all":
        for name, agent in agents.items():
            print(agent.report())
            print("-" * 30)
        return

    if agent_name not in agents:
        print(f" Agente desconhecido '{agent_name}'.")
        print("   Available: " + ", ".join(agents.keys()))
        return
        
    target_agent = agents[agent_name]
    
    if action:
        # EXECUTE MODE
        print(f" DISPATCHING ORDER: [{agent_name.upper()}] -> {action.upper()}")
        result = target_agent.execute_task(action)
        print(f"    Result: {result}")
    else:
        # REPORT MODE
        print(target_agent.report())

if __name__ == "__main__":
    # Usage: python3 omega_commander.py [agent] [action]
    # ex: python3 omega_commander.py sniper attack
    # ex: python3 omega_commander.py shield panic
    # ex: python3 omega_commander.py brain
    
    agent_arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    action_arg = sys.argv[2] if len(sys.argv) > 2 else None
    
    dispatch(agent_arg, action_arg)
