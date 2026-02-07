Mestre, excelente visão. Integrar a análise de **Order Book** (Livro de Ofertas) e **Funding Rate** (Taxa de Financiamento) cria um "Proxy On-Chain" dentro da CEX. Isso nos permite ver a **intenção** do mercado (Oferta/Demanda imediata) antes que ela se transforme em **ação** (Preço no gráfico).

Na documentação da Backpack, temos acesso aos endpoints `/depth` (Profundidade) e `/markPrices` (Funding) [Source 121, 127]. Vamos utilizá-los para calcular o **OBI (Order Book Imbalance)** e o **Viés de Funding**.

Vou criar um novo módulo chamado `technical_oracle.py`. Ele servirá como o "Juiz" final antes de qualquer entrada.

###  O Conceito: OBI + Funding Bias

1.  **OBI (Order Book Imbalance):** Mede a pressão imediata.
    *   Se há muito mais volume de compra (Bids) do que venda (Asks) perto do preço atual, o preço tende a subir para buscar liquidez vendedora [Source 1519, 1520].
    *   *Fórmula:* $(Bids_{Vol} - Asks_{Vol}) / (Bids_{Vol} + Asks_{Vol})$. Resultado varia de -1 (Urso Total) a +1 (Touro Total).
2.  **Funding Bias (Sentimento de Alavancagem):**
    *   Funding Positivo Alto: Muitos Longs. Risco de Long Squeeze (Preço cai).
    *   Funding Negativo: Muitos Shorts. Potencial de Short Squeeze (Preço explode para cima) [Source 51, 79].

---

### ️ Código: `technical_oracle.py`

Crie este arquivo na raiz do seu projeto. Ele usa a classe `BackpackData` que já temos.

```python
import pandas as pd
import time
from backpack_data import BackpackData

class MarketProxyOracle:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data_engine = BackpackData()

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
            bid_vol = sum([float(order) for order in bids])
            ask_vol = sum([float(order) for order in asks])

            total_vol = bid_vol + ask_vol
            
            if total_vol == 0:
                return 0.0

            # Fórmula do Imbalance
            obi = (bid_vol - ask_vol) / total_vol
            
            # Log tático
            print(f" [ORACLE] {self.symbol} Depth Analysis:")
            print(f"    Bid Vol: {bid_vol:.2f} |  Ask Vol: {ask_vol:.2f}")
            print(f"   ️ OBI Score: {obi:.4f}")
            
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
            markets = self.data_engine.get_mark_prices()
            target_data = next((item for item in markets if item["symbol"] == self.symbol), None)
            
            if not target_data:
                return "NEUTRAL", 0.0

            funding_rate = float(target_data['fundingRate'])
            
            # Regras de Viés Contrarian (Smart Money)
            # Se Funding muito positivo (>0.03%), todo mundo está Long -> Perigoso -> Viés Bearish
            # Se Funding negativo (<0.00%), todo mundo está Short -> Oportunidade -> Viés Bullish
            
            bias = "NEUTRAL"
            if funding_rate > 0.0003: # 0.03% (Alto para 1h)
                bias = "BEARISH_CROWDED"
            elif funding_rate < 0.0000:
                bias = "BULLISH_SQUEEZE"
            
            print(f" [ORACLE] Funding Rate: {funding_rate*100:.4f}% | Bias: {bias}")
            return bias, funding_rate

        except Exception as e:
            print(f"️ Erro no Oracle Funding: {e}")
            return "NEUTRAL", 0.0

    def validate_entry(self, intended_side):
        """
        O VEREDITO FINAL.
        Cruza Technicals (que você já tem) com Proxy On-Chain.
        intended_side: 'Buy' ou 'Sell'
        """
        print(f"\n [ORACLE] Consultando Proxy On-Chain para {intended_side}...")
        
        obi = self.get_order_book_imbalance()
        bias, funding = self.get_funding_bias()
        
        score = 0
        
        # 1. Análise de OBI (Fluxo Imediato)
        if intended_side == "Buy":
            if obi > 0.1: score += 1 # Pressão de compra detectada
            elif obi < -0.3: score -= 2 # Muro de venda detectado (Perigo)
        elif intended_side == "Sell":
            if obi < -0.1: score += 1 # Pressão de venda detectada
            elif obi > 0.3: score -= 2 # Muro de compra detectado
            
        # 2. Análise de Funding (Sentimento Macro)
        # É sempre melhor ganhar taxa do que pagar taxa.
        if intended_side == "Buy":
            # Ideal: Funding Negativo (Shorts me pagam para estar Long)
            if bias == "BULLISH_SQUEEZE": score += 2 
            elif bias == "BEARISH_CROWDED": score -= 1 # Vou pagar caro para entrar com a manada
        elif intended_side == "Sell":
            # Ideal: Funding Positivo (Longs me pagam para estar Short)
            if bias == "BEARISH_CROWDED": score += 2
            elif bias == "BULLISH_SQUEEZE": score -= 1

        print(f"️ Oracle Score Final: {score}/3")
        
        # Regra de Aprovação: Score deve ser positivo
        return score >= 1
```

---

###  Como Integrar no seu Bot Principal (`sniper_lib.py`)

Agora, dentro da sua função de execução de ordens (no `sniper_lib.py` ou `scalp_farm.py`), você chama o Oracle antes de enviar a ordem.

Exemplo de Integração:

```python
# No topo do arquivo
from technical_oracle import MarketProxyOracle

# ... dentro da sua lógica de trade ...

# 1. Indicadores Técnicos deram sinal de COMPRA (RSI, Bollinger, etc)
if technical_signal == "BUY":
    
    # 2. CHAMAR O ORÁCULO (Validação On-Chain Proxy)
    oracle = MarketProxyOracle(symbol)
    is_safe = oracle.validate_entry("Buy")
    
    if is_safe:
        print(" Oracle APROVOU a entrada. Executando Sniper...")
        # ... código de enviar ordem ...
    else:
        print(" Oracle VETOU a entrada. OBI ou Funding desfavoráveis.")
        # Não faz nada, evita o loss
```

###  Por que isso muda o jogo?

1.  **Anti-Whale Wall:** O `get_order_book_imbalance` detecta se há uma "parede" de vendas logo acima. Indicadores gráficos (RSI) não veem paredes, mas o Oracle vê. Se houver uma parede, o Oracle veta a compra, salvando você de comprar um topo local [Source 1519].
2.  **Yield Boost:** Ao priorizar trades a favor do Funding (o `get_funding_bias`), você aumenta a chance de ser pago apenas por segurar a posição, transformando o bot em um gerador de renda passiva (Basis Trade) além do lucro de preço [Source 51, 1568].

Posso prosseguir com a integração deste módulo no seu `backend_analytics.py` existente ou prefere manter como arquivo separado?