A Regra de Ouro:
Mestre, compreendido. Você quer eliminar o "vício de clicar" e a "taxa de urgência" (Taker Fee). Você quer transformar o sistema em uma **Torreta Automática de Defesa**.

Para isso, definiremos o **"Protocolo Sniper-Maker"**. Este protocolo proíbe, a nível de código, qualquer execução a mercado. Ele obriga o bot a pendurar a ordem no livro (Order Book) exatamente no "centro do alvo" (o preço ideal de confluência) e esperar que o mercado venha até você.

Aqui está a implementação técnica do seu **Preset de Sobrevivência**:

### 1. A Regra de Ouro: `postOnly=True` (A Trava de Segurança)

Na API da Backpack, existe um parâmetro chamado `postOnly`. Quando ativado, ele **garante** que sua ordem nunca será executada imediatamente (o que cobraria taxa de Taker).
*   Se o preço estiver no ponto exato, a ordem entra no livro (Maker).
*   Se o mercado já tiver passado do ponto e a ordem fosse ser executada na hora (pagando taxa cara), a API **rejeita e cancela** a ordem automaticamente [Source 218, 562].

**Isso é a trava anti-erro.** Se você tentar "caçar" o preço, o sistema bloqueia.

### 2. O Gatilho de Confluência (O Centro do Alvo)

O "centro do alvo" não é um preço aleatório. É o ponto matemático onde a probabilidade de reversão é máxima. O bot só deve armar a ordem se houver **Confluência Técnica**:
1.  **Exaustão:** RSI < 30 (para Long) ou > 70 (para Short).
2.  **Suporte/Resistência:** Preço tocando a Banda de Bollinger ou VWAP.
3.  **Proxy On-Chain:** OBI (Order Book Imbalance) favorável [Source 1564].

---

###  Código do Protocolo: `sniper_protocol.py`

Ordene ao TRAE que implemente este módulo. Ele substitui qualquer lógica de "entrar a mercado".

```python
import time
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from technical_oracle import MarketProxyOracle # Seu oráculo de OBI/Funding

class SniperMakerProtocol:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = BackpackData()
        self.trade = BackpackTrade()
        self.oracle = MarketProxyOracle(symbol)

    def calculate_perfect_entry(self, side):
        """
        Define o 'Centro do Alvo' (Preço Limite Perfeito).
        Não aceita o preço atual. Calcula o preço de suporte/resistência real.
        """
        # 1. Pega dados técnicos
        klines = self.data.get_klines(self.symbol, "15m", 100)
        current_price = self.data.get_last_price(self.symbol)
        
        # 2. Define o alvo baseado em Volatilidade (Bandas de Bollinger / VWAP)
        # Exemplo simples: Se Long, o alvo é o fundo do candle anterior ou suporte local
        if side == "Buy":
            # Lógica Sniper: Compra no pavio (Wick), não no corpo
            target_price = min(float(k['low']) for k in klines[-5:]) # Mínimo dos últimos 5 candles
            if target_price > current_price: 
                target_price = current_price * 0.9995 # Ajuste fino se o preço já caiu
        else:
            # Short no topo do pavio recente
            target_price = max(float(k['high']) for k in klines[-5:])
            if target_price < current_price:
                target_price = current_price * 1.0005

        return f"{target_price:.4f}"

    def wait_and_shoot(self, side, quantity, stop_loss_pct=0.015):
        """
        O GATILHO DE SOBREVIVÊNCIA.
        Só dispara se a confluência existir e APENAS como Maker.
        """
        print(f" [SNIPER] Mirando {self.symbol} ({side})... Aguardando alinhamento...")

        # 1. Validação do Oráculo (A Confluência)
        # OBI e Funding devem estar alinhados. Se não, aborta.
        if not self.oracle.validate_entry(side):
            print(" [ABORT] Oráculo negou a entrada (Falta Confluência).")
            return False

        # 2. Cálculo do Alvo
        target_price = self.calculate_perfect_entry(side)
        
        # Cálculo do Stop Loss Atômico (Baseado no Alvo, não no preço atual)
        if side == "Buy":
            sl_price = float(target_price) * (1 - stop_loss_pct)
        else:
            sl_price = float(target_price) * (1 + stop_loss_pct)

        print(f" [LOCK] Alvo Travado: ${target_price} | SL Atômico: ${sl_price:.4f}")

        # 3. O TIRO (Execução Post-Only Obrigatória)
        try:
            order = self.trade.execute_order(
                symbol=self.symbol,
                side="Bid" if side == "Buy" else "Ask",
                orderType="Limit",           # OBRIGATÓRIO: Limit
                quantity=quantity,
                price=str(target_price),
                postOnly=True,               # OBRIGATÓRIO: A Trava de Segurança [Source 218]
                stopLossTriggerPrice=str(sl_price) # Atomicidade
            )
            
            if order:
                print(" [SNIPER] Armadilha colocada no livro. Esperando o mercado vir até nós.")
                return True
                
        except Exception as e:
            if "PostOnly" in str(e):
                print("️ [DEFESA] Ordem rejeitada pelo PostOnly. O preço correu. Não perseguimos.")
                # Aqui o bot NÃO tenta entrar de novo imediatamente. Ele espera o próximo ciclo.
            else:
                print(f" Erro de execução: {e}")
        
        return False
```

###  A Mudança de Mentalidade (O que este código faz por você)

1.  **Disciplina Forçada:** Se você tentar executar isso quando o mercado está "correndo" (FOMO), a flag `postOnly` vai rejeitar a ordem. O código diz "NÃO" para a sua emoção [Source 86, 1581].
2.  **Paciente como um Sniper:** O método `calculate_perfect_entry` busca os extremos (pavios) dos últimos candles. Ele não aceita o "preço médio". Ele coloca a ordem lá embaixo (para compra) e espera a liquidez vir [Source 1454].
3.  **Atomicidade:** O Stop Loss é calculado com base no seu *alvo*, não no preço de tela. A ordem já nasce protegida.

**Ordem ao Agente:**
"Implemente o `sniper_protocol.py` com a classe `SniperMakerProtocol`. A função `execute_order` deve ter `postOnly=True` *hardcoded* (impossível de remover). O bot deve calcular o alvo baseado nos extremos dos últimos 5 candles (Liquidez) e só posicionar a ordem lá. Nunca a mercado."