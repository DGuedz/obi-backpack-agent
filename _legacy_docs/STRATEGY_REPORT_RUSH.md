#  Relatório de Estratégia: RUSH EXPONENCIAL (Machine Gun Mode)

**Data:** 26/01/2026
**Objetivo:** Volume Massivo ($1M) e Recuperação de Saldo ($250).
**Status Atual:** 🟢 ATIVO

---

## 1. Configuração Atual (Machine Gun)

Esta configuração foi desenhada para maximizar o giro de capital (turnover) e capturar micro-movimentos com alta alavancagem.

| Parâmetro | Valor | Justificativa |
| :--- | :--- | :--- |
| **Alavancagem** | **12x** | Growth Mode. Aumenta o volume nocional e o ROI percentual. |
| **Take Profit (TP)** | **1.5%** | Scalping. Garante saídas rápidas antes de reversões. Foco em win-rate. |
| **Stop Loss (SL)** | Dinâmico (ATR) | Proteção contra crash, mas flexível para volatilidade. |
| **OBI Threshold** | **0.12** | Alta sensibilidade. Entra cedo no fluxo de ordens. |
| **Scan Interval** | 0.5s / 3s | Varredura frenética para não perder nenhum pump/dump. |
| **Assets** | Top Liquid + Alpha | BTC, ETH, SOL, MON, SUI, APT, etc. (Liquidez garantida). |
| **Risk Reserve** | 5% | All-In Mode. Maximiza capital em jogo. |

### Lógica de Entrada (Sniper)
1.  **Trend Surfing:** Se SMA200 for Bullish e OBI > 0.12, COMPRA.
2.  **Bollinger Scalp:** Se preço furar banda (3m) e reverter, entra contra-tendência (Scalp rápido).
3.  **Funding Ignorado:** Se houver fluxo forte, ignora taxas de funding negativas.

---

## 2. Diagnóstico e Pontos de Melhoria

Para atingir o volume agressivo de forma sustentável, identificamos os seguintes gargalos e soluções:

###  Gargalo 1: Capital Estagnado (Dead Capital)
**Problema:** Posições que ficam "de lado" (choppy) por 10-15 minutos travam a margem que poderia estar girando em outro ativo.
**Solução:** **Stagnation Killer (Matador de Estagnação).**
*   **Ação:** Se uma posição não mover > 0.5% em 10 minutos, encerrar imediatamente (Market Close).
*   **Benefício:** Libera margem para novas oportunidades de fluxo. Volume requer movimento.

###  Gargalo 2: Latência Sequencial
**Problema:** O bot analisa um ativo por vez (`await`). Se o ativo 1 demora 1s para responder, o ativo 10 só é analisado 10s depois.
**Solução:** **Async Prefetching (Paralelismo).**
*   **Ação:** Disparar requisições de dados (Orderbook, Candles) para todos os 15 ativos simultaneamente.
*   **Benefício:** Reduz o tempo de ciclo de 30s para < 3s. Reação instantânea a pumps.

###  Gargalo 3: Entrada Única (Single Bullet)
**Problema:** Entrar com 100% da mão em um ponto pode levar a stops desnecessários em ruídos.
**Solução:** **Micro-Laddering (Escada Rápida).**
*   **Ação:** Dividir a entrada em 3 ordens: 40% a Mercado, 30% em -0.1%, 30% em -0.2%.
*   **Benefício:** Melhora o preço médio e reduz violinações. (Implementação complexa, prioridade média).

---

## 3. Plano de Ação Imediato

1.  **Implementar Stagnation Killer:** Adicionar monitoramento de tempo/preço no loop principal.
2.  **Otimizar Latência:** Refatorar o loop de scan para usar `asyncio.gather` na coleta de dados.
3.  **Monitorar Performance:** Acompanhar o crescimento do Volume vs. Taxas pagas.

---
*Relatório gerado automaticamente pelo Agente Trae.*
