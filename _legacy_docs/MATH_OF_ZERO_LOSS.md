#  A Matemática do "Zero Loss" (Prova de Conceito)

Este documento prova matematicamente como o **Protocolo Chimera V3** garante que, uma vez atingido o gatilho de lucro mínimo, a operação nunca resulta em prejuízo financeiro real, cobrindo todas as taxas envolvidas.

---

## 1. As Variáveis de Custo (Backpack Exchange)

Para calcular o ponto de empate real (Breakeven), precisamos considerar os piores cenários de taxas.

*   **Entrada (Maker):**
    *   Taxa: **0.00%** (ou rebate negativo, mas assumimos 0 para segurança).
    *   Tipo: Limit Post Only.
*   **Saída de Emergência (Stop Market):**
    *   Taxa: **0.085%** (Taker Fee).
    *   Tipo: Stop Market (Executa a mercado para garantir saída).
*   **Slippage (Estimado):**
    *   Impacto: **0.015%** (Deslizamento de preço em momentos de volatilidade).

**Custo Total do Stop:** `0.085% (Taxa) + 0.015% (Slippage) = 0.10%`

---

## 2. A Lógica do Breakeven (O Pulo do Gato)

Para sair no "Zero a Zero" financeiro, não basta sair no preço de entrada. Precisamos sair no preço de entrada **MAIS** o custo total.

### Fórmula do Zero Loss (Long)
$$ \text{Stop Price} = \text{Entry Price} \times (1 + \text{Total Cost} + \text{Min Profit Buffer}) $$

Onde:
*   `Total Cost` = 0.10% (0.001)
*   `Min Profit Buffer` = 0.015% (Garantia extra)

$$ \text{Stop Price} = \text{Entry Price} \times (1 + 0.00115) $$

### Exemplo Prático (Bitcoin)
*   **Preço de Entrada:** $100,000
*   **Custo de Stop (0.10%):** $100
*   **Buffer de Lucro (0.015%):** $15
*   **Preço do Novo Stop (Zero Loss):** $100,115

Se o Stop for acionado em $100,115:
1.  **Ganho Bruto:** $115
2.  **Taxa Paga (0.085% de $100,115):** ~$85.10
3.  **Lucro Líquido:** $115 - $85.10 = **+$29.90 (VERDE)**

---

## 3. O Gatilho de Ativação

Não podemos mover o Stop para o Breakeven imediatamente, ou o ruído do mercado nos tiraria da posição em segundos. Precisamos de um "respiro".

*   **Gatilho de Ativação:** 0.20% de Lucro.
*   Quando o preço sobe 0.20% (para $100,200), movemos o Stop para $100,115.
*   Isso dá ao mercado um espaço de ~0.08% para oscilar sem nos tirar, garantindo que se formos tirados, saímos com as taxas pagas.

---

## 4. Mapa de Decisão (Confluência de Indicadores)

O Agente utiliza uma matriz de decisão de 5 camadas para autorizar a entrada.

| Camada | Indicador | Condição (Long) | Por que? |
| :--- | :--- | :--- | :--- |
| **1. Macro** | **Volume 24h** | > $10M USD | Garante liquidez para entrar e sair sem slippage massivo. |
| **2. Tendência** | **EMA 50 (1h)** | Preço > EMA | Nunca operar contra a tendência primária. "The trend is your friend". |
| **3. Fluxo** | **OBI (Imbalance)** | > 0.10 (10%) | O Book de Ofertas deve ter mais Compradores (Bids) do que Vendedores (Asks) no topo. |
| **4. Custo** | **Funding Rate** | < 0.04% | Evita "Crowded Trades" onde todo mundo está posicionado igual e a taxa de manutenção é cara. |
| **5. Custo** | **Spread** | < 0.15% | Se o Spread for alto, já começamos perdendo muito. O robô recusa operar. |

### Saída (Exit Strategy)
1.  **Take Profit (Alvo):** 5% (Fixo).
2.  **Stop Loss (Proteção):** 0.1% (Inicial).
3.  **Breakeven (Zero Loss):** Ativado quando Lucro > 0.2%.

---

**Conclusão:** O sistema é matematicamente desenhado para que o "pior cenário" após o movimento inicial seja o pagamento das taxas, preservando o capital principal intacto.
