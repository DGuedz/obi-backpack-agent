import math

class VSCTransformer:
    """
     VSC: Volume-Sentiment-Correlation Transformer
    Módulo de Refinamento de Leitura OBI para Detecção de Armadilhas (Traps).
    
    Objetivo: Identificar 'Fake Liquidity' e 'Exhaustion Moves' (Armadilhas).
    """
    
    def __init__(self):
        pass
        
    def analyze(self, book):
        """
        Analisa o Livro de Ofertas e retorna um Score de Qualidade (VSC Score).
        Retorna:
            - vsc_score (float): -1.0 a 1.0 (Força Ajustada)
            - trap_signal (str): "NONE", "BULL_TRAP", "BEAR_TRAP"
            - confidence (float): 0.0 a 1.0
        """
        if not book:
            return 0.0, "NONE", 0.0
            
        bids = book.get('bids', [])
        asks = book.get('asks', [])
        
        if not bids or not asks:
            return 0.0, "NONE", 0.0
            
        # 1. Volume Profile Analysis (Weighted Depth)
        # Mais peso para ordens próximas ao spread (Real Intent)
        # Menos peso para ordens distantes (Spoofing Potential)
        
        bid_power = 0.0
        ask_power = 0.0
        
        # Analisar Top 20 levels
        limit = min(len(bids), len(asks), 20)
        
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2
        
        for i in range(limit):
            # Bid Analysis
            bp = float(bids[i][0])
            bq = float(bids[i][1])
            # Distance Weight: Decay exponencial com a distância
            dist_b = abs(mid_price - bp) / mid_price
            weight_b = math.exp(-100 * dist_b) # Ajuste de sensibilidade
            bid_power += (bq * bp) * weight_b
            
            # Ask Analysis
            ap = float(asks[i][0])
            aq = float(asks[i][1])
            dist_a = abs(ap - mid_price) / mid_price
            weight_a = math.exp(-100 * dist_a)
            ask_power += (aq * ap) * weight_a
            
        # 2. VSC Score Calculation (Weighted OBI)
        total_power = bid_power + ask_power
        vsc_score = (bid_power - ask_power) / total_power if total_power > 0 else 0
        
        # 3. Trap Detection (Liquidity Vacuum)
        # Se o Spread for muito alto comparado à profundidade imediata -> Vacuum
        spread_pct = (best_ask - best_bid) / best_bid
        
        # Calcular densidade imediata (Top 3 levels)
        top3_bid_vol = sum([float(b[1]) for b in bids[:3]])
        top3_ask_vol = sum([float(a[1]) for a in asks[:3]])
        
        trap_signal = "NONE"
        confidence = 0.0
        
        # Bull Trap Logic:
        # Preço subindo (implícito se VSC Score alto?) Não, aqui olhamos a estrutura do book.
        # Bull Trap Estrutural: Paredão de Venda sumindo (Low Ask Power) mas sem compra real (Low Bid Power).
        # "Vacuum Up" -> Sobe no vácuo para ser vendido lá em cima.
        if spread_pct > 0.001: # Spread > 0.1% (Alto para scalping)
             if top3_ask_vol < top3_bid_vol * 0.1: # Asks muito finos comparado aos Bids
                 trap_signal = "BULL_TRAP_VACUUM" # Cuidado, pode subir rápido e devolver tudo
                 confidence = 0.8
                 
        # Bear Trap Logic:
        # Paredão de Compra sumindo, preço cai no vácuo.
        if spread_pct > 0.001:
             if top3_bid_vol < top3_ask_vol * 0.1:
                 trap_signal = "BEAR_TRAP_VACUUM"
                 confidence = 0.8
                 
        # Spoofing Check
        # Se VSC Score é muito alto (+0.8), mas Top 3 levels são fracos -> Fake Wall distante
        if vsc_score > 0.5 and top3_bid_vol < (bid_power * 0.05):
            trap_signal = "SPOOF_BUY_WALL" # Tem muito volume longe, mas nada perto
            vsc_score *= 0.5 # Penaliza o score
            
        if vsc_score < -0.5 and top3_ask_vol < (ask_power * 0.05):
            trap_signal = "SPOOF_SELL_WALL"
            vsc_score *= 0.5 # Penaliza
            
        return vsc_score, trap_signal, confidence

