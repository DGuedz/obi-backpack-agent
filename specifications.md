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
