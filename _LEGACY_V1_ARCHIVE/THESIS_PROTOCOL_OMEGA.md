# ️ PROTOCOL OMEGA: The DoubleGreen Thesis
**Data:** 2026-01-16  
**Status:** ACTIVE (Live Fire)  
**Versão:** 1.0 (Genesis)

---

## 1. Visão Geral (The Vision)
O **Protocolo Omega** não é apenas um conjunto de bots; é uma infraestrutura de **Hedge Fund Autônomo**. 
Nosso objetivo é capturar valor em todo o espectro do mercado cripto, unindo a eficiência de execução das **CEX (Centralized Exchanges)** com as oportunidades de rendimento e incentivos da **DeFi (Decentralized Finance)**.

**A Filosofia:**
> *"Gerar na CEX, Proteger no Código, Multiplicar na DeFi."*

---

## 2. Arquitetura Técnica (The Tech Stack)

O sistema opera em um ambiente Python modular, segregado em três camadas de responsabilidade:

### A. Camada de Execução (Trading Engines)
*   **️ Weaver Grid (Market Maker):**
    *   *Função:* Captura de spread e volatilidade em `SOL_USDC_PERP`.
    *   *Lógica:* Grid Trading dinâmico com espaçamento de 0.15% e alavancagem 3x.
    *   *Diferencial:* Rebalanceamento automático ("Recalibration") baseado em fluxo de ordens.
*   ** Phoenix V2 (Momentum Hunter):**
    *   *Função:* Entradas cirúrgicas em `BTC` e `ETH`.
    *   *Lógica:* RSI Extremo (<30 / >70) + Cruzamento de EMAs.
    *   *Diferencial:* Execução 100% Maker (Taxas negativas/rebate).

### B. Camada de Conectividade (The Nexus)
*   ** Wormhole Nexus (`execute_bridge.py`):**
    *   *Função:* Ponte automatizada de liquidez entre Backpack CEX e Fogo Chain.
    *   *Tecnologia:* Integração direta com `solana-py` e `solders` para assinatura on-chain de transações Wormhole.
    *   *Meta:* Maximizar XP na campanha "Fogo Blaze" reciclando lucros de trading.

### C. Camada de Defesa (The Shield)
*   **️ Sentinel Protocol (`sentinel_protocol.py`):**
    *   *Função:* Gestão de risco em tempo real (24/7).
    *   *Regras:* Stop Loss Rígido (-1.9%), Breakeven Dinâmico (+0.5%).
*   ** Shadow Guard (`shadow_guard.py`):**
    *   *Função:* Kill-switch de emergência.
    *   *Capacidade:* Drenagem total de fundos on-chain para Cold Wallet em <2 segundos via comando secreto.

---

## 3. Estratégia Financeira (The Alpha)

Dividimos o capital em dois departamentos com mandatos distintos:

### Departamento A: "Spec Ops" (Trading Ativo)
*   **Capital:** 60-70% (Alocado na Backpack Exchange).
*   **Foco:** Crescimento Agressivo Controlado.
*   **Ativos:** SOL (Grid), BTC/ETH (Scalp).
*   **Métrica de Sucesso:** PnL Diário > 1%.

### Departamento B: "Iron Bank" (Delta Neutro / Yield)
*   **Capital:** 30-40% (Alocado On-Chain/LFG Wallet).
*   **Foco:** Preservação e Renda Passiva.
*   **Estratégia:**
    1.  **Spot Long:** Comprar ativo (ex: SOL).
    2.  **Perp Short:** Vender mesmo valor nocional em Perp.
    3.  **Resultado:** Variação de preço anulada. Lucro vem de **Funding Rates** (pagos por traders alavancados) + **Incentivos DeFi** (Airdrops).

---

## 4. O Ciclo Operacional (The Flywheel)

1.  **Geração:** Weaver e Phoenix geram lucro em USDC na Backpack.
2.  **Triangulação:** O lucro excedente é sacado para a Wallet Main via `execute_bridge.py`.
3.  **Expansão:** O capital na Wallet é enviado via Wormhole para Fogo Chain (gerando XP/Volume).
4.  **Retorno:** O capital retorna para a CEX (`return_to_base.py`) para compor a margem e aumentar o tamanho das operações do Weaver.

---

## 5. Procedimentos de Segurança (SOP)

*   **Chaves:** Armazenadas exclusivamente em variáveis de ambiente (`.env`), nunca hardcoded.
*   **Permissões:** API Keys com restrição de IP (recomendado).
*   **Emergência:** Em caso de comprometimento, executar:
    `python3 shadow_guard.py --code BlueHorizon`

---

**Assinado:** DoubleGreen & Trae AI.
*Building the Future of Algo-Trading.*