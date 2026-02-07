# Plano de Recuperação de Capital: "Missão $100"

## 1. O Objetivo Matemático
Recuperar **$100.00** de lucro líquido a partir do capital atual, utilizando a estratégia de "Volume Farming" e "Profit Snowball" com as seguintes premissas:

*   **Tamanho da Posição (Size):** $20.00 (Fixo)
*   **Alavancagem:** 5x (Poder de Compra efetivo: $100.00 por trade)
*   **Take Profit (TP):** 0.5% (Movimento do Preço) = 2.5% ROI (Alavancado)
*   **Lucro por Trade (Target):** $20.00 * 2.5% = **$0.50**

### A Equação da Recuperação
Para atingir $100.00, precisamos de:
`$100.00 / $0.50 = 200 Trades Vencedores`

Isso parece muito, mas com o **Loop Mode** e **HFT Frequency**, podemos executar de 20 a 50 trades por dia.

*   **Meta Diária:** 20 Trades Vencedores ($10.00/dia)
*   **Tempo Estimado:** 10 dias de operação consistente.

## 2. A Estratégia "Smart Money Loop"

O sistema foi recalibrado para operar em **Loop Fechado**:

1.  **Entrada:** A Mercado (Taker) em ativos com **Whale OBI** (Baleias comprando) e **Tendência Confirmada (1m/3m/5m)**.
2.  **Proteção:** Trailing Stop Micro-Scalp.
    *   Assim que o lucro bate **0.12%**, o Stop sobe para o 0x0. Risco eliminado.
    *   Assim que bate **0.25%**, garantimos lucro.
3.  **Saída:** TP fixo em 0.5% ou Stop no lucro.
4.  **Recarga:** Assim que uma posição fecha, a margem é liberada e o bot abre IMEDIATAMENTE a próxima oportunidade da fila.

## 3. Regras de Ouro (Risk Management)

*   **Max Loss por Trade:** $0.10 (Hard Stop). Se o trade andar contra 0.1% (Preço) / 0.5% (ROI), cortamos.
*   **Exposição Máxima:** 5 Posições simultâneas ($100 de Notional Value).
*   **Hedge Dinâmico:** Se tivermos muitos Longs, o bot priorizará Shorts para equilibrar o Delta do portfólio.

## 4. Acompanhamento de Progresso

Implementaremos um **Contador de Lucro da Sessão** no Radar OBI para você ver cada centavo sendo somado rumo aos $100.

> "Centavos somam Dólares. Dólares somam a Recuperação."
