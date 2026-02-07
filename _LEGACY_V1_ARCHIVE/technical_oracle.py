import os
import time
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

class MarketProxyOracle:
    def __init__(self, symbol, auth=None, data_engine=None):
        self.symbol = symbol
        if auth and data_engine:
            self.auth = auth
            self.data_engine = data_engine
        else:
            # Fallback to creating new connection if not provided (Modular standalone)
            from dotenv import load_dotenv
            load_dotenv()
            self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
            self.data_engine = BackpackData(self.auth)

    def get_order_book_imbalance(self, depth_limit=20):
        """
        Calcula o OBI (Order Book Imbalance).
        Analisa as top N ordens do book para determinar a pressão.
        Retorna: float entre -1.0 (Venda Forte) e 1.0 (Compra Forte)
        """
        try:
            depth = self.data_engine.get_depth(self.symbol)
            if not depth:
                return 0.0

            bids = depth.get('bids', [])[:depth_limit]
            asks = depth.get('asks', [])[:depth_limit]

            # Somar volume (Quantidade) das ofertas próximas
            bid_vol = sum([float(order[1]) for order in bids])
            ask_vol = sum([float(order[1]) for order in asks])

            total_vol = bid_vol + ask_vol
            
            if total_vol == 0:
                return 0.0

            # Fórmula do Imbalance
            obi = (bid_vol - ask_vol) / total_vol
            
            # Log tático
            # print(f" [ORACLE] {self.symbol} Depth Analysis:")
            # print(f"    Bid Vol: {bid_vol:.2f} |  Ask Vol: {ask_vol:.2f}")
            # print(f"   ️ OBI Score: {obi:.4f}")
            
            return obi

        except Exception as e:
            print(f"️ Erro no Oracle OBI: {e}")
            return 0.0

    def get_funding_bias(self):
        """
        Analisa o Funding Rate para determinar se o mercado está 'Crowded'.
        Retorna: 'BEARISH' (Muitos Longs), 'BULLISH' (Muitos Shorts) ou 'NEUTRAL'
        """
        try:
            # Assuming get_tickers gives all tickers with funding info
            tickers = self.data_engine.get_tickers()
            target_data = next((item for item in tickers if item["symbol"] == self.symbol), None)
            
            if not target_data:
                # Try specific ticker endpoint fallback if bulk fails
                target_data = self.data_engine.get_ticker(self.symbol)
            
            if not target_data:
                return "NEUTRAL", 0.0

            # Backpack API usually provides 'fundingRate' in ticker data for Perps
            # Note: Field name might vary, checking generic access
            funding_rate = float(target_data.get('fundingRate', 0.0))
            
            # Regras de Viés Contrarian (Smart Money)
            # Se Funding muito positivo (>0.03%), todo mundo está Long -> Perigoso -> Viés Bearish
            # Se Funding negativo (<0.00%), todo mundo está Short -> Oportunidade -> Viés Bullish
            
            bias = "NEUTRAL"
            if funding_rate > 0.0003: # 0.03% (Alto para 1h)
                bias = "BEARISH_CROWDED"
            elif funding_rate < 0.0000:
                bias = "BULLISH_SQUEEZE"
            
            # print(f" [ORACLE] Funding Rate: {funding_rate*100:.4f}% | Bias: {bias}")
            return bias, funding_rate

        except Exception as e:
            print(f"️ Erro no Oracle Funding: {e}")
            return "NEUTRAL", 0.0

    def validate_entry(self, intended_side):
        """
        O VEREDITO FINAL.
        Cruza Technicals (que você já tem) com Proxy On-Chain.
        intended_side: 'Bid' (Buy) ou 'Ask' (Sell)
        """
        print(f" [ORACLE] Consultando Proxy On-Chain para {intended_side}...")
        
        obi = self.get_order_book_imbalance()
        bias, funding = self.get_funding_bias()
        
        score = 0
        
        # 1. Análise de OBI (Fluxo Imediato)
        if intended_side == "Bid": # Buying
            if obi > 0.1: score += 1 # Pressão de compra detectada
            elif obi < -0.3: score -= 2 # Muro de venda detectado (Perigo)
        elif intended_side == "Ask": # Selling
            if obi < -0.1: score += 1 # Pressão de venda detectada
            elif obi > 0.3: score -= 2 # Muro de compra detectado
            
        # 2. Análise de Funding (Sentimento Macro)
        # É sempre melhor ganhar taxa do que pagar taxa.
        if intended_side == "Bid":
            # Ideal: Funding Negativo (Shorts me pagam para estar Long)
            if bias == "BULLISH_SQUEEZE": score += 2 
            elif bias == "BEARISH_CROWDED": score -= 1 # Vou pagar caro para entrar com a manada
        elif intended_side == "Ask":
            # Ideal: Funding Positivo (Longs me pagam para estar Short)
            if bias == "BEARISH_CROWDED": score += 2
            elif bias == "BULLISH_SQUEEZE": score -= 1

        print(f"   ️ Oracle Score Final: {score}/3 (OBI: {obi:.2f}, Bias: {bias})")
        
        # Regra de Aprovação: Score deve ser positivo
        return score >= 1
