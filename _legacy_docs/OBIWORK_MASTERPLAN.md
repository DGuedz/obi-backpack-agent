#  OBIWORK MASTERPLAN
# Arquitetura Técnica & Roadmap do Produto

## 1. Visão do Produto
O **OBIWORK** é um sistema de trading institucional automatizado ("HFT Lite") projetado para operar na Backpack Exchange.
Ele diferencia-se por utilizar **OBI (Order Book Imbalance)** como sinal primário de fluxo, em vez de indicadores técnicos atrasados (RSI, MACD).

**Proposta de Valor:** "Don't Trust. Verify."
- Execução em milissegundos (< 45ms).
- Proteção de Capital Atômica (Stop Loss On-Chain).
- Auditoria Visual (Landing Page com Terminal Ao Vivo).

---

## 2. Arquitetura do Sistema

### A. Core Engine (`obiwork_core/`)
O cérebro do sistema, escrito em Python para performance e robustez.

*   **`volume_farmer.py`**: O executor principal.
    *   *Modo Straddle*: Gera volume delta-neutral (Market Maker).
    *   *Modo Surf*: Segue tendências baseadas em OBI forte (> 0.25).
    *   *Anti-Reversal Guard*: Fecha posições instantaneamente se o fluxo virar.
    *   *S4 Finale Mode*: Configuração agressiva (BTC Only, 5x Lev) para maximizar volume/pontos.
*   **`backpack_transport.py`**: Camada de transporte HTTP/API.
    *   Assinatura ED25519 nativa.
    *   Tratamento de erros de rate-limit e payloads.
*   **`technical_oracle.py`**: O analista de dados.
    *   Cálculo de OBI (Bids vs Asks).
    *   Detecção de Spoofing (Paredes falsas).
    *   Verificação de Saúde do Ativo (ATR, Funding).

### B. Interface Web (`obiwork_web/`)
A vitrine do produto e hub de gestão, construída em Next.js + Tailwind + Framer Motion.

*   **`Hero Section`**: Estética Cyberpunk/Terminal.
*   **`ProofSection`**: Dados reais de volume e ranking (Social Proof).
*   **`TerminalSimulation`**: Componente React que simula o log do bot em tempo real.
*   **`PricingSection`**: Checkout ($997) e conexão de carteira.
*   **`MentorshipHub`**: Área do aluno com integração Google Calendar.
    *   *Service Account*: Autenticação segura server-side (JWT).
    *   *Eventos*: Listagem dinâmica de aulas e links do Meet.

---

## 3. Estratégia de Trading (Algoritmo)

1.  **Sinal (Trigger)**:
    *   Monitora o Order Book (Depth) via WebSocket/Polling.
    *   Calcula `OBI = (BidVol - AskVol) / TotalVol`.
    *   Se `OBI > 0.4` (Bullish) ou `OBI < -0.4` (Bearish) -> **Gatilho**.

2.  **Entrada (Execution)**:
    *   Envia ordem `Limit PostOnly` (Maker) para economizar taxas.
    *   Preço ajustado dinamicamente para garantir fill rápido (Front-run leve).

3.  **Proteção (Safety)**:
    *   **Imediato**: Envia ordem `Stop Market` com `triggerQuantity` para travar prejuízo máximo.
    *   **Monitoramento**: Se OBI inverter sinal (ex: era +0.4, virou -0.5), ativa `Emergency Exit` (Market Close).

4.  **Saída (Profit)**:
    *   **Scalp**: Take Profit curto (0.1% - 0.5%) para girar volume.
    *   **Surf**: Trailing Stop para surfar tendências maiores.

---

## 4. Roadmap de Desenvolvimento

- [x] **Fase 1: MVP (Core)**
    - [x] Conexão API Backpack (Leitura/Escrita).
    - [x] Cálculo OBI Básico.
    - [x] Execução Maker/Taker.
    - [x] Stop Loss Atômico (Correção Payload aplicada).

- [x] **Fase 2: Interface (Web)**
    - [x] Landing Page Next.js.
    - [x] Terminal Simulator UI.
    - [x] Integração de Badges e Stats.
    - [x] Mentorship Hub (Google Calendar API).

- [ ] **Fase 3: Refinamento (Alpha)**
    - [ ] Migração completa para WebSocket (menor latência).
    - [ ] Painel de Controle Web (Dashboard Admin).
    - [ ] Backtest Engine com dados históricos.

- [ ] **Fase 4: Produto Final (V1.0)**
    - [ ] Instalador Universal (`setup.py` validado).
    - [ ] Documentação para Cliente Final.
    - [ ] Sistema de Licenciamento via NFT/Token.

---
*Documento Mestre - OBIWORK Labs*
