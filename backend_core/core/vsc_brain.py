import logging
from core.vsc_neuro_translator import VSCNeuroTranslator

class VSCBrain:
    """
    CÉREBRO VSC (Cognitive Validation Engine).
    Arquitetura de 4 Camadas: Percepção -> Contexto -> Memória -> Validação.
    Responsável por aprovar ou vetar entradas com base em Score Determinístico.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("VSCBrain")
        self.translator = VSCNeuroTranslator()
        # Estado cognitivo atual (pode ser persistido)
        self.current_state = {
            "perception": [],
            "score": 100,
            "decision": "WAIT"
        }

    def validate_entry(self, symbol, proposed_action, market_data):
        """
        Valida uma intenção de entrada (LONG/SHORT).
        Retorna: (Bool, String Reason, Float SizeFactor)
        """
        # 1. PERCEPÇÃO (Tradução)
        vsc_states = self.translator.translate(market_data)
        self.current_state["perception"] = vsc_states
        
        # 2. CONTEXTO & SCORE (Cálculo Determinístico)
        score = 100
        reasons = []
        
        # Extrair dados crus para vetos absolutos (às vezes precisamos do número exato para o veto)
        funding = market_data.get('funding', 0)
        rsi = market_data.get('rsi', 50)
        obi = market_data.get('obi', 0)

        # --- REGRAS DE VETO ABSOLUTAS (HARD BLOCK) ---
        # "Se acontecer isso, NÃO ENTRA, independente do score."
        
        # Veto 1: Late Entry (Comprar topo)
        if proposed_action == "LONG" and rsi > 75:
            return False, f" VETO: Late Entry (RSI {rsi} > 75)", 0.0
        if proposed_action == "SHORT" and rsi < 25:
            return False, f" VETO: Late Entry (RSI {rsi} < 25)", 0.0

        # Veto 2: Fighting the Flow (OBI Contra)
        if proposed_action == "LONG" and obi < -0.3:
            return False, f" VETO: Fighting Orderbook (OBI {obi:.2f} < -0.3)", 0.0
        if proposed_action == "SHORT" and obi > 0.3:
            return False, f" VETO: Fighting Orderbook (OBI {obi:.2f} > 0.3)", 0.0

        # Veto 3: Crowded Trade (Funding muito alto/baixo)
        if proposed_action == "LONG" and funding > 0.0005:
             return False, f" VETO: Crowded Long (Funding {funding} High)", 0.0
        if proposed_action == "SHORT" and funding < -0.0005:
             return False, f" VETO: Crowded Short (Funding {funding} Negative)", 0.0


        # --- SCORE ANTI-FAKE-MOVE (PENALIDADES) ---
        # Começa em 100. Perde pontos por sinais ruins.
        
        # Penalidade: Funding adverso (mas não suficiente para veto)
        if 'funding_rate,high' in vsc_states and proposed_action == "LONG":
            score -= 20
            reasons.append("funding_high")
        elif 'funding_rate,negative' in vsc_states and proposed_action == "SHORT":
            score -= 20
            reasons.append("funding_negative")
        
        # Penalidade: Netflow Positivo (Entrada de tokens na exchange = Pressão de Venda)
        if 'exchange_netflow,positive_inflow' in vsc_states and proposed_action == "LONG":
            score -= 35
            reasons.append("netflow_inflow_danger")
            
        # Penalidade: OI Colapsando (Perda de interesse/Liquidez)
        if 'open_interest,collapsing' in vsc_states:
            score -= 15
            reasons.append("oi_collapsing")

        # Penalidade: Smart Money Distribuindo (se detectado)
        if 'smart_money,active_distribution' in vsc_states and proposed_action == "LONG":
            score -= 25
            reasons.append("whale_distribution")

        # Penalidade: Fighting Trend (RSI divergence mild)
        if proposed_action == "LONG" and rsi < 40: # Trying to catch a falling knife without extreme oversold
             score -= 10
             reasons.append("weak_momentum")
        
        # Atualiza estado
        self.current_state["score"] = score
        
        # 3. VALIDAÇÃO FINAL (Gate)
        THRESHOLD_OPTIMAL = 70
        THRESHOLD_CAUTIOUS = 50
        
        decision_str = ""
        size_factor = 0.0
        result = False

        if score >= THRESHOLD_OPTIMAL:
            self.current_state["decision"] = "APPROVED"
            decision_str = f" APPROVED (Score: {score})"
            size_factor = 1.0
            result = True
        elif score >= THRESHOLD_CAUTIOUS:
            self.current_state["decision"] = "CAUTIOUS"
            decision_str = f"️ CAUTIOUS_APPROVED (Score: {score}) - MICROSIZE MODE"
            size_factor = 0.1 # 10% do tamanho normal
            result = True
        else:
            self.current_state["decision"] = "REJECTED"
            decision_str = f" REJECTED (Score: {score}, Reasons: {reasons})"
            size_factor = 0.0
            result = False
            
        self.save_state()
        return result, decision_str, size_factor

    def save_state(self):
        try:
            # Caminho absoluto ou relativo
            path = "tools/brain_state.vsc"
            with open(path, "w") as f:
                f.write("# === VSC BRAIN STATE ===\n")
                f.write(f"last_score,{self.current_state['score']}\n")
                f.write(f"last_decision,{self.current_state['decision']}\n")
                for tag in self.current_state['perception']:
                    f.write(f"perception,{tag}\n")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def get_brain_state(self):
        return self.current_state
