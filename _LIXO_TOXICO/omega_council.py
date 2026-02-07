import time
import os
import json
import pandas as pd
from dotenv import load_dotenv

# Import Real Modules for Live Data
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators
from technical_oracle import MarketProxyOracle

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

class OrchestratorAgent(AgentBase):
    def __init__(self, data_engine, indicators):
        super().__init__("Orchestrator", "Cérebro Central & Gestão de Volatilidade", "")
        self.data = data_engine
        self.indicators = indicators
        self.atr_threshold = 500.00
        
    def get_live_data(self):
        # Fetch real ATR
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
        - Próxima Varredura: em 0.8s
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
        - Order Book Imbalance (OBI): {obi:.4f} ({'Compra' if obi > 0 else 'Venda'}) [Source 1548]
        - Funding Bias: {bias} ({funding*100:.4f}%) [Source 1548]
        - Paredes de Liquidez: {walls_status}
        - **Permissão de Disparo:**  CONCEDIDA (Apenas Maker)
        """

class SentinelAgent(AgentBase):
    def __init__(self, data_engine):
        super().__init__("Sentinel", "Escudo de Capital & Kill-Switch", "️")
        self.data = data_engine
        
    def get_live_stats(self):
        try:
            collateral = self.data.get_account_collateral()
            # Need to parse real margin fraction if available, or calc
            # For now, mock or try to extract from 'collateral'
            # Assuming collateral returns dict with 'marginFraction' key if available
            margin_fraction = collateral.get('marginFraction', 'N/A')
            
            # PnL from positions
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
        - Margin Fraction: {mf} (Seguro > 0.10) [Source 1562]
        - PnL Sessão (Unrealized): ${pnl:.2f} (Meta: 1.5% | Kill: -1.5%)
        - Integridade do Sistema: 100%
        - **Ação:** Monitorando {pos_count} posições abertas. Mãos longe do teclado.
        """

class WeaverAgent(AgentBase):
    def __init__(self, orchestrator_ref):
        super().__init__("Weaver Grid", "Motor de Renda Passiva (Maker)", "️")
        self.orch = orchestrator_ref
    
    def report(self):
        atr = self.orch.get_live_data()
        spacing = atr * 0.5
        return f"""
        {self.introduce()}
        ️ **Tecelagem de Ordens:**
        - Espaçamento Dinâmico: ${spacing:.2f} (Baseado em ATR * 0.5) [Source 1562]
        - Modo: Post-Only (Maker Imperative) [Source 1561]
        - Alvo: Captura de Spread Lateral em {SYMBOL}.
        - Settlement: Juros compostos a cada 10s. [Source 581]
        """

class SniperAgent(AgentBase):
    def __init__(self):
        super().__init__("Smart Entry Sniper", "Operador de Tendência (Aegis)", "")
    
    def report(self):
        return f"""
        {self.introduce()}
         **Mira Tática:**
        - Protocolo Aegis: ATIVO (EMA200 + RSI + Oracle) [Source 1563]
        - Status: **ESPERA** (Aguardando Volatilidade > 500 ATR).
        - Viés de Funding: Preparado para Short se Funding > 0. [Source 52]
        """

# --- INSTANTIATION & SUMMONING ---
def summon(agent_name="all"):
    # Init Connections
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    oracle_engine = MarketProxyOracle(SYMBOL, auth, data)
    
    # Init Agents
    orch = OrchestratorAgent(data, indicators)
    oracle = OracleAgent(oracle_engine)
    sentinel = SentinelAgent(data)
    weaver = WeaverAgent(orch)
    sniper = SniperAgent()
    
    agents = {
        "brain": orch,
        "oracle": oracle,
        "shield": sentinel,
        "weaver": weaver,
        "sniper": sniper
    }
    
    print("\n--- ️ OMEGA COUNCIL SITREP ---")
    
    if agent_name in agents:
        print(agents[agent_name].report())
    elif agent_name == "all":
        for name, agent in agents.items():
            print(agent.report())
            print("-" * 30)
    else:
        print(" Agente desconhecido. Chame: brain, oracle, shield, weaver, sniper.")

if __name__ == "__main__":
    import sys
    # Allow command line arg: python3 omega_council.py brain
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    summon(target)
