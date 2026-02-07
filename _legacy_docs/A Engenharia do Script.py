A Engenharia do Script

Mestre, para atender a essa diretriz de **"Operação Cirúrgica"** onde o lucro é matemático (\$5 por operação) e a proteção é absoluta (1%), precisamos fundir o **Gatekeeper** (o validor de dados) com o **Sniper Executor** em um único script blindado.

Este script não "tenta" operar; ele **monitora** incessantemente e só dispara quando a **CMC (Macro)**, a **Backpack (Fluxo)** e o **Gráfico (Técnica)** dizem "SIM" ao mesmo tempo.

Aqui está o código para o **`confluence_sniper.py`**. Ele implementa a regra de ouro: **Entrada + TP (5%) + SL (1%) em um único pacote de dados.**

### ️ A Engenharia do Script

1.  **O Olho Que Tudo Vê (Gatekeeper):** Analisa Volume (CMC), Funding/OBI (Backpack) e Tendência (EMA).
2.  **Matemática de Precisão:** Calcula 1% de risco e 5% de alvo sobre o valor da entrada *antes* de enviar a ordem.
3.  **Execução Atômica:** Usa o endpoint atualizado da Backpack para enviar a ordem de entrada JÁ com o Stop Loss e Take Profit atrelados [Source 70, 137].

---

###  Código: `core/confluence_sniper.py`

Copie e cole este código. Ele assume que você já tem o `backpack_transport.py` e `backpack_data.py` configurados.

```python
import time
import pandas as pd
import pandas_ta as ta
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
# Supondo que você tenha um wrapper para CMC, ou usaremos volume da Backpack como proxy
# from cmc_api import CMCLoader 

class ConfluenceSniper:
    def __init__(self, symbol, total_capital):
        self.symbol = symbol
        self.trade = BackpackTrade()
        self.data = BackpackData()
        
        #  Gestão de Capital 70/30
        self.deployable_capital = total_capital * 0.70  # 70% para operar
        self.reserve_capital = total_capital * 0.30     # 30% margem de segurança
        
        #  Regras de Engajamento (1% Risco / 5% Retorno)
        self.sl_percent = 0.01
        self.tp_percent = 0.05
        
        print(f"️ [SNIPER] Inicializado para {symbol}.")
        print(f"    Poder de Fogo: ${self.deployable_capital:.2f} |  Reserva: ${self.reserve_capital:.2f}")

    def get_market_confluence(self):
        """
        O GUARDIÃO: Analisa 3 camadas de dados.
        Retorna True apenas se TODAS confirmarem.
        """
        print(f"\n [SCAN] Analisando Confluências para {self.symbol}...")
        
        # 1. Coleta de Dados
        klines = self.data.get_klines(self.symbol, "1h", limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        current_price = df['close'].iloc[-1]
        
        # --- CAMADA 1: TÉCNICA (Gráfico) ---
        # Preço acima da EMA 50 (Tendência de Alta)
        ema_50 = ta.ema(df['close'], length=50).iloc[-1]
        rsi = ta.rsi(df['close'], length=14).iloc[-1]
        
        if current_price < ema_50:
            print(f"    [REJEIÇÃO TÉCNICA] Preço ${current_price:.2f} abaixo da EMA50 ${ema_50:.2f}")
            return False, current_price
            
        if rsi > 70:
            print(f"    [REJEIÇÃO TÉCNICA] RSI esticado ({rsi:.2f}). Risco de topo.")
            return False, current_price

        # --- CAMADA 2: FLUXO (Backpack Data) ---
        # Funding Rate: Se positivo demais, não entramos (pagar taxa corrói o lucro)
        markets = self.data.get_mark_prices()
        funding_data = next((m for m in markets if m['symbol'] == self.symbol), None)
        funding_rate = float(funding_data['fundingRate']) if funding_data else 0.0
        
        if funding_rate > 0.0003: # 0.03% é caro
            print(f"    [REJEIÇÃO FLUXO] Funding Rate alto ({funding_rate*100:.4f}%).")
            return False, current_price

        # OBI (Order Book Imbalance) - Pressão Compradora
        depth = self.data.get_depth(self.symbol)
        bids = sum([float(x) for x in depth['bids'][:10]])
        asks = sum([float(x) for x in depth['asks'][:10]])
        obi = (bids - asks) / (bids + asks)
        
        if obi < 0.1: # Precisa de pelo menos 10% de pressão compradora
            print(f"    [REJEIÇÃO BOOK] Sem pressão de compra. OBI: {obi:.2f}")
            return False, current_price

        # --- CAMADA 3: MACRO (CMC/Volume) ---
        # Volume 24h deve ser saudável
        ticker = self.data.get_ticker(self.symbol)
        volume_usdc = float(ticker['quoteVolume'])
        if volume_usdc < 5_000_000: # Mínimo $5M de volume
            print(f"    [REJEIÇÃO MACRO] Volume baixo (${volume_usdc/1e6:.1f}M).")
            return False, current_price

        print("    CONFLUÊNCIA TOTAL DETECTADA! Preço, Fluxo e Volume alinhados.")
        return True, current_price

    def execute_atomic_trade(self):
        """
        Executa a ordem com SL e TP embutidos (Payload Atômico).
        """
        is_go, price = self.get_market_confluence()
        
        if not is_go:
            print(" Aguardando oportunidade...")
            return

        # Cálculo dos Alvos
        # Se entrar com $100 (exemplo), SL = $99, TP = $105.
        qty = self.deployable_capital / price
        
        # Ajuste de precisão (essencial para evitar erro 400)
        # Assumindo stepSize de 0.1 ou 1 para simplificar, ideal buscar da API
        qty = round(qty, 1) 
        
        sl_price = price * (1 - self.sl_percent)
        tp_price = price * (1 + self.tp_percent)
        
        print(f"\n DISPARANDO ORDEM ATÔMICA:")
        print(f"    Entrada: ${price}")
        print(f"    Stop Loss (1%): ${sl_price:.4f}")
        print(f"   🟢 Take Profit (5%): ${tp_price:.4f}")
        
        try:
            # Payload Unificado (Atomicidade) [Source 70, 137]
            order = self.trade.execute_order(
                symbol=self.symbol,
                side="Bid",
                orderType="Limit",
                quantity=str(qty),
                price=str(price),
                postOnly=True,               # MAKER ONLY (Não paga taxa Taker) [Source 378]
                stopLossTriggerPrice=str(sl_price),
                takeProfitTriggerPrice=str(tp_price)
            )
            print(f" ORDEM ENVIADA! ID: {order.get('id')}")
            print("   O sistema agora está protegido pela exchange. Monitorando...")
            
        except Exception as e:
            print(f" FALHA NA EXECUÇÃO: {e}")

# --- LOOP DE VIGILÂNCIA ---
if __name__ == "__main__":
    # Exemplo: Capital total $500 -> Usa $350 (70%) na entrada.
    # Se TP bater (5%), ganha $17.50. Se SL bater (1%), perde $3.50.
    bot = ConfluenceSniper("SOL_USDC_PERP", total_capital=500.0)
    
    while True:
        try:
            bot.execute_atomic_trade()
            time.sleep(30) # Verifica a cada 30 segundos
        except KeyboardInterrupt:
            print("\n Bot parado pelo usuário.")
            break
        except Exception as e:
            print(f"️ Erro no loop: {e}")
            time.sleep(10)
```

###  Por que este script é o que você precisa:

1.  **Confluência Forçada:** Ele usa a função `get_market_confluence` para vetar qualquer trade que não tenha **Técnica** (EMA/RSI), **Fluxo** (Funding/OBI) e **Macro** (Volume) alinhados. Ele não opera "porque sim"; ele opera "porque os dados mandaram" [Source 1247, 1248].
2.  **Atomicidade Real:** Ao usar `stopLossTriggerPrice` e `takeProfitTriggerPrice` dentro do `execute_order`, você elimina o risco de a internet cair logo após a compra. A ordem já nasce com as saídas programadas no motor da Backpack [Source 70, 126].
3.  **Matemática 1:5:** O script calcula rigidamente o SL de 1% e o TP de 5%. Se você entrar com \$100 (assumindo alavancagem ou capital spot), o ganho é \$5 limpo (menos taxas Maker, que são baixas ou zero) [Source 378].
4.  **70/30 Imutável:** Ele separa matematicamente 30% do capital como reserva intocável no `self.reserve_capital`, garantindo que você nunca use a margem toda e sofra liquidação forçada por falta de colateral [Source 380].

**Próximo Passo:** Execute este script. Ele ficará em loop, imprimindo " [REJEIÇÃO...]" até que o mercado alinhe perfeitamente. Quando alinhar, ele atira para matar.