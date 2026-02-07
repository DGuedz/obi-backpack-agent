import logging
import sys
import os
from typing import List, Dict, Tuple
from collections import deque
import statistics

# Adicionar path raiz para importar módulos irmãos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar Camada VSC
from tools.vsc_transformer import VSCLayer

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MarketProxyOracle")

class MarketProxyOracle:
    """
    Oráculo de Proxy de Mercado (AI-Vetting Layer).
    Analisa o buffer VSC para detectar manipulação (Spoofing/Whale Walls)
    e vetar sinais de trade falsos antes da execução.
    """

    def __init__(self, vsc_layer: VSCLayer):
        self.vsc = vsc_layer
        self.min_obi_threshold = 0.25 # Mínimo de desequilíbrio para considerar sinal forte
        self.volatility_cap = 0.02 # 2% de spread máximo aceitável para entrada

    def decode_context(self, vsc_context: List[str]) -> List[Dict]:
        """Decodifica o histórico VSC do buffer para análise estruturada"""
        decoded_history = []
        for entry in vsc_context:
            if entry.startswith("DPT"):
                parts = entry.split('|')
                # Format: DPT|SYMBOL|BEST_BID|BEST_ASK|SPREAD
                try:
                    decoded_history.append({
                        "symbol": parts[1],
                        "best_bid": float(parts[2]),
                        "best_ask": float(parts[3]),
                        "spread": float(parts[4])
                    })
                except (IndexError, ValueError):
                    continue
        return decoded_history

    def analyze_liquidity_health(self, symbol: str) -> Tuple[bool, str]:
        """
        Analisa a saúde da liquidez recente (Buffer VSC).
        Retorna (Aprovado, Razão).
        """
        context = self.vsc.get_market_proxy_context(symbol)
        if not context:
            return False, "NO_CONTEXT_DATA"

        history = self.decode_context(context)
        if len(history) < 3:
            return False, "INSUFFICIENT_SAMPLES"

        # 1. Análise de Spread (Volatilidade Implícita)
        avg_spread = statistics.mean([h['spread'] for h in history])
        last_price = history[-1]['best_bid']
        
        spread_ratio = avg_spread / last_price if last_price > 0 else 1.0
        
        if spread_ratio > self.volatility_cap:
            return False, f"HIGH_SPREAD_RISK|{spread_ratio*100:.2f}%"

        # 2. Detecção de 'Fading Liquidity' (Bid/Ask sumindo rápido)
        # Se o spread aumentou drasticamente no último snapshot vs média
        last_spread = history[-1]['spread']
        if last_spread > (avg_spread * 2.0):
             return False, "LIQUIDITY_FADING|SpreadSpike"

        return True, "LIQUIDITY_HEALTHY"

    def veto_signal(self, symbol: str, signal_side: str, obi_score: float) -> Tuple[bool, str]:
        """
        Decide se VETA ou APROVA um sinal de trade.
        Usa lógica 'Spec-Driven' para filtrar ruído.
        """
        # 1. Check Básico de OBI
        if abs(obi_score) < self.min_obi_threshold:
            return True, f"WEAK_OBI|{obi_score:.2f}<{self.min_obi_threshold}"

        # 2. Check de Coerência (Sinal vs OBI)
        # OBI Positivo = Pressão de Compra (Bid > Ask)
        # OBI Negativo = Pressão de Venda (Ask > Bid)
        if signal_side.lower() == 'buy' and obi_score < -0.1:
            return True, f"DIVERGENCE|Signal:Buy|OBI:{obi_score:.2f}"
        
        if signal_side.lower() == 'sell' and obi_score > 0.1:
            return True, f"DIVERGENCE|Signal:Sell|OBI:{obi_score:.2f}"

        # 3. Análise Profunda de Liquidez (VSC Buffer)
        is_healthy, reason = self.analyze_liquidity_health(symbol)
        if not is_healthy:
            return True, f"LIQUIDITY_VETO|{reason}"

        return False, "APPROVED" # False = Não Vetado (Aprovado)

# --- Teste Unitário Rápido ---
if __name__ == "__main__":
    vsc_test = VSCLayer()
    oracle = MarketProxyOracle(vsc_test)
    
    symbol = "SOL_USDC"
    
    # Simular histórico no buffer VSC
    # DPT|SYMBOL|BID|ASK|SPREAD
    history_samples = [
        f"DPT|{symbol}|24.50|24.51|0.01",
        f"DPT|{symbol}|24.50|24.51|0.01",
        f"DPT|{symbol}|24.49|24.52|0.03", # Spread aumentando
        f"DPT|{symbol}|24.45|24.55|0.10"  # Spread explodiu (Panic/Illiquidity)
    ]
    
    print(f"--- MarketProxyOracle Test: {symbol} ---")
    
    # 1. Popular Buffer
    for sample in history_samples:
        # Mocking buffer injection direct string since we are testing Oracle logic
        vsc_test.scout_buffer.setdefault(symbol, deque()).append(sample)
        
    # 2. Teste de Análise de Liquidez
    healthy, reason = oracle.analyze_liquidity_health(symbol)
    print(f"Liquidity Health: {healthy} -> {reason}")
    
    # 3. Teste de Veto (Cenário: Sinal de Compra em mercado volátil)
    vetoed, reason = oracle.veto_signal(symbol, "buy", 0.5) # OBI forte, mas spread ruim
    print(f"Signal Veto (Buy, OBI 0.5): {vetoed} -> {reason}")
    
    # 4. Limpar e Testar Cenário Saudável
    vsc_test.scout_buffer[symbol].clear()
    good_samples = [f"DPT|{symbol}|24.50|24.51|0.01"] * 5
    for s in good_samples: vsc_test.scout_buffer[symbol].append(s)
    
    vetoed_good, reason_good = oracle.veto_signal(symbol, "buy", 0.4)
    print(f"Signal Veto (Buy, OBI 0.4, Good Liq): {vetoed_good} -> {reason_good}")
