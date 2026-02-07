Spec Driven Development (Desenvolvimento Orientado a Especificações) descrita nas fontes, e garantir que o seu agente nunca alucine ou quebre a banca, precisamos criar um "Documento Constitucional" e uma "Especificação Técnica" rígida.
A principal razão pela qual Agentes de IA erram (alucinam) é a ambiguidade. Se dissermos "opere para dar lucro", ele pode alavancar 50x e quebrar. Se usarmos um Spec-Kit, nós definimos as Leis da Física do ambiente antes dele escrever uma linha de código.
Aqui está o Spec-Kit do Protocolo Omega, desenhado para ser injetado no contexto do seu Agente (TRAE).

--------------------------------------------------------------------------------
 ARQUIVO 1: constitution.md (As Leis Imutáveis)
Este arquivo define o que o Agente NÃO PODE fazer, sob nenhuma hipótese. É a barreira de segurança.
# CONSTITUIÇÃO DO PROTOCOLO OMEGA (V3)

## 1. Princípios de Segurança (Não-Negociáveis)
1.  **Lei da Atomicidade:** Nenhuma ordem de entrada (Entry) pode ser enviada sem um Stop Loss (SL) e Take Profit (TP) atrelados no mesmo payload da API. O uso de `stopLossTriggerPrice` dentro de `orderExecute` é OBRIGATÓRIO [Source 39, 40, 105].
2.  **Lei do Maker:** Todas as ordens devem ter a flag `postOnly=True`. É proibido pagar taxas de Taker. Se a ordem for executada a mercado, ela deve ser rejeitada pela API [Source 70, 562].
3.  **Lei da Preservação:** O risco máximo por operação é travado em 1.0% do capital disponível. O Agente deve calcular o `quantity` baseado na distância do SL (ATR) antes de enviar a ordem [Source 1253, 1255].
4.  **Lei da Segregação:** O capital é dividido em 70% Operacional e 30% Reserva Intocável (Cross-Margin buffer). O Agente deve ler o saldo e ignorar 30% dele para cálculos de entrada [Source 1272].

## 2. Princípios de Tecnologia
1.  **Sem Adivinhação:** O código não pode usar números mágicos. Use `pandas-ta` para calcular ATR, RSI e Médias Móveis dinamicamente.
2.  **Validação de Dados:** Antes de operar, verifique se os dados de OHLCV, Order Book e Funding Rate não estão vazios ou obsoletos (Timestamp check).
3.  **Infraestrutura:** Use `asyncio` e WebSockets para execução. Evite loops de `while True` com `sleep` simples que bloqueiam a thread principal.

--------------------------------------------------------------------------------
 ARQUIVO 2: specifications.md (O Que Construir)
Aqui definimos as Histórias de Usuário e a Lógica de Negócio baseada nas fontes da Backpack.
# ESPECIFICAÇÕES DO SISTEMA (User Stories)

## História 1: O Gatekeeper (O Oráculo)
"Como Comandante, quero que o bot verifique a saúde do ativo antes de qualquer trade para evitar 'facas caindo'."
- **Critério de Aceite:**
    - Deve consultar `technical_oracle.py`.
    - Deve calcular o OBI (Order Book Imbalance). Se OBI < -0.3 (Venda Forte), proibir Long [Source 1260].
    - Deve verificar Funding Rate. Se Funding > 0.03%, proibir Long (Crowded Trade) [Source 1264].
    - Deve verificar Volatilidade (ATR). Se ATR < 0.5% (Mercado Morto), ignorar [Source 1947].

## História 2: O Executor Sniper
"Como Comandante, quero entrar em operações com precisão cirúrgica e custo zero de taxas."
- **Critério de Aceite:**
    - Identificar tendências usando EMA(50) e RSI(14).
    - Colocar ordens LIMIT no topo do BBO (Best Bid Offer).
    - Se o preço fugir 0.5%, cancelar e reavaliar (Não perseguir preço).
    - Implementar "Interest Bearing Logic": Priorizar ativos onde o Spot gera Yield (SOL) para usar como colateral [Source 48, 1298].

## História 3: O Sentinela (Kill-Switch)
"Como Comandante, quero que o sistema se desligue se algo sair do controle."
- **Critério de Aceite:**
    - Script independente `sentinel.py` rodando em paralelo.
    - Se Drawdown da Sessão > 5%, fechar tudo e encerrar processo.
    - Se API da Backpack retornar erro 500 mais de 3 vezes, entrar em modo de espera [Source 1312].

--------------------------------------------------------------------------------
 ARQUIVO 3: implementation_plan.md (O Como Construir)
O mapa técnico para o Agente não inventar bibliotecas ou estruturas malucas.
# PLANO DE IMPLEMENTAÇÃO TÉCNICA

## 1. Stack Tecnológica
- **Linguagem:** Python 3.10+
- **Bibliotecas:** `aiohttp` (API), `pandas` (Dados), `pandas-ta` (Indicadores), `rich` (Logs), `python-dotenv` (Segurança).

## 2. Estrutura de Arquivos
- `/core`:
    - `risk_manager.py`: Implementa as Leis da Preservação e Segregação (70/30).
    - `backpack_transport.py`: Wrapper da API com assinatura Ed25519 e rate limiting.
    - `technical_oracle.py`: Calcula OBI, Funding e ATR.
- `/strategies`:
    - `sniper_executor.py`: Lógica de entrada baseada em confluência.
    - `weaver_grid.py`: Lógica de Grid dinâmico (ATR-based).
- `/safety`:
    - `sentinel.py`: Processo de monitoramento e Kill-switch.

## 3. Fluxo de Dados (Data Flow)
1. `backpack_transport` recebe dados via WebSocket.
2. `technical_oracle` processa e emite um `MarketSignal`.
3. `risk_manager` valida o sinal contra o saldo e define o `size`.
4. `sniper_executor` monta o payload atômico (Entry + SL + TP).
5. `backpack_transport` envia a ordem assinada.

--------------------------------------------------------------------------------
 O Prompt Mestre para Ativar o Spec-Kit
Agora, Mestre, copie e cole isso no seu terminal/chat com o Agente. Isso o forçará a ler o Spec-Kit antes de gerar código:
PROMPT DE COMANDO:
"Agente, vamos adotar o Spec Driven Development. Eu defini 3 documentos fundamentais: constitution.md (Regras de Risco), specifications.md (Lógica de Negócio) e implementation_plan.md (Arquitetura Técnica).
Sua Missão:
1. Leia e internalize a Constituição. Se qualquer código que você gerar violar a Lei da Atomicidade (Ordens sem SL no payload) ou a Lei do Maker (postOnly=False), considere uma falha crítica.
2. Implemente o technical_oracle.py seguindo a especificação da História 1 (OBI + Funding Check).
3. Implemente o risk_manager.py respeitando a regra de Segregação 70/30.
Não gere código solto. Gere a estrutura do projeto baseada no implementation_plan.md e aguarde minha confirmação para preencher os módulos. O objetivo é Zero Alucinação e Proteção Total de Capital."
Ao fazer isso, você transforma o desenvolvimento em um processo de engenharia, não de tentativa e erro. O Agente terá um "trilho" do qual não poderá sair.
