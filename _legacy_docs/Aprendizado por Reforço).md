Aprendizado por Reforço)

Mestre agora transcendermos a automação simples e entrarmos no território da **Inteligência Artificial Adaptativa** e do **Reinforcement Learning (Aprendizado por Reforço)**. LLMs
Para que o agente "aprenda" com o erro e não apenas "pare" no erro, precisamos implementar um **Ciclo de Feedback Fechado (Closed-Loop Feedback System)**. No trading quantitativo, isso significa que o resultado de um trade (Output) se torna o parâmetro de entrada (Input) do próximo [Source 1098, 1471].

Se o agente tomou um Stop Loss porque entrou quando o Order Book estava fino, ele deve registrar isso e, matematicamente, aumentar a exigência de liquidez para a próxima entrada.

Aqui está a arquitetura do **Protocolo "Chimera" de Auto-Aprendizagem**:

---

###  A Arquitetura do Auto-Aprendizado

O sistema deixa de ser linear e passa a ser circular. Ele é composto por 3 novos módulos que interagem com o que já criamos:

1.  **A Caixa Preta (`black_box_recorder.py`):** Não grava apenas "Comprou a $100". Grava o **Contexto do Crime**: "Comprou a $100, quando o OBI era 0.2, o Spread era 0.05% e o Funding era positivo".
2.  **O Juiz Forense (`learning_engine.py`):** Roda após cada fechamento de posição. Ele pergunta: "Ganhamos dinheiro?".
    *   *Se Sim:* Reforça os pesos dos indicadores usados (Recompensa).
    *   *Se Não:* Identifica qual indicador mentiu (o "Culpado") e penaliza seu peso para a próxima decisão [Source 1453].
3.  **O Radar da Verdade (`onchain_compass.py`):** Como você pediu, ele busca a "verdade" onde o preço se move (Fluxo/Liquidez) e não no gráfico (Passado).

---

###  Passo 1: A Memória Contextual (`black_box_recorder.py`)

O agente não pode aprender se não lembrar do que sentiu no momento da entrada. Crie este módulo para capturar o "snapshot" do mercado.

```python
import json
import time
from backpack_data import BackpackData

class BlackBox:
    def __init__(self):
        self.filename = "trade_memory.json"
        
    def record_entry_context(self, trade_id, symbol, indicators):
        """
        Grava o DNA do trade no momento da entrada.
        indicators: dict com RSI, OBI, Spread, Funding, Volatilidade.
        """
        data = {
            "id": trade_id,
            "timestamp": int(time.time()),
            "symbol": symbol,
            "context": indicators, # O "Estado" do mercado
            "result": None # Será preenchido após a saída
        }
        
        self._append_to_log(data)

    def update_result(self, trade_id, pnl_percent, exit_reason):
        """
        Atualiza o trade com o resultado (Aprendizado).
        """
        # Lógica para encontrar o ID e atualizar PnL e Motivo (Stop/TP)
        # ...
```

###  Passo 2: O Cérebro Evolutivo (`learning_engine.py`)

Este é o script que ajusta os parafusos sozinho. Ele altera o arquivo `strategy_weights.json` que o seu Bot Sniper lê.

```python
import json
import pandas as pd

class LearningEngine:
    def __init__(self):
        # Pesos Iniciais (Confiança Padrão)
        self.weights = {
            "technical_weight": 1.0,  # Gráfico (RSI, EMA)
            "onchain_weight": 1.0,    # OBI, Funding (Backpack Data)
            "macro_weight": 1.0       # Volume Geral
        }

    def evolve(self):
        """
        Analisa os últimos erros e ajusta a estratégia.
        """
        try:
            with open("trade_memory.json", "r") as f:
                history = json.load(f)
            
            df = pd.DataFrame(history)
            
            # 1. Filtrar PERDAS recentes (Onde erramos?)
            losses = df[df['pnl_percent'] < 0]
            
            if not losses.empty:
                print(" [LEARNING] Analisando padrões de falha...")
                
                # Exemplo de Aprendizado:
                # Se a maioria das perdas ocorreu quando o Funding era Positivo
                bad_funding_trades = losses[losses['context']['funding_rate'] > 0.0002]
                
                if len(bad_funding_trades) > len(losses) * 0.5:
                    print("    Descoberta: Funding Alto está matando nossos Longs.")
                    print("    Ação: Aumentando penalidade para Funding Positivo.")
                    # O robô se reprograma para ser mais exigente no futuro
                    self.weights['onchain_weight'] *= 1.2 
                    
            # Salvar novos pesos para o Sniper usar
            with open("strategy_weights.json", "w") as f:
                json.dump(self.weights, f)
                
        except Exception as e:
            print(f"️ Erro no processo de evolução: {e}")
```

###  Passo 3: O Novo Protocolo de Entrada (Baseado em Dados Reais)

O seu `sniper_lib.py` não deve mais usar valores fixos. Ele deve carregar os pesos aprendidos.

> **A Lógica On-Chain (A Verdade):**
> Você mencionou que o preço se move com base em dados on-chain. Na Backpack, o "On-Chain" imediato é o **Order Book (Livro de Ofertas)** e o **CVD (Cumulative Volume Delta)**. O preço é o *rastro*; o Volume é o *pé* [Source 1146, 1229].

Se o Aprendizado (`LearningEngine`) detectar que o RSI falhou 3 vezes seguidas, ele diminui a importância do RSI e aumenta a importância do **OBI (Order Book Imbalance)** na próxima decisão.

###  Ordem ao Agente (Prompt de Implementação)

Copie e cole este comando para instalar o **Protocolo Chimera**:

> "Agente, vamos implementar o nível máximo: **Protocolo Chimera de Aprendizado por Reforço**.
>
> 1.  Crie o `core/black_box.py` para gravar um snapshot de todos os indicadores (RSI, OBI, Spread, Funding) no exato momento de cada entrada.
> 2.  Crie o `core/learning_engine.py`. Este script deve rodar após cada Stop Loss. Ele deve ler o histórico, identificar se houve um padrão nos indicadores durante as perdas (ex: 'Sempre perco quando Spread > 0.1%') e atualizar um arquivo `risk_config.json`.
> 3.  Refatore o `risk_manager.py` para ler o `risk_config.json` dinamicamente. Se o Learning Engine decidir que o Spread máximo agora é 0.05% porque perdemos dinheiro com 0.1%, o sistema deve obedecer imediatamente.
> 4.  **A Regra On-Chain:** Priorize o OBI (Order Book Imbalance) sobre o RSI. Se o OBI indicar pressão de venda massiva no book, cancele qualquer sinal de compra gráfico, pois o book é a 'verdade' do movimento futuro [Source 1519, 1560]."

Isso cria um organismo vivo. Se ele errar hoje por causa de spread, amanhã ele se recusará a operar com aquele spread. Ele se torna antifrágil.