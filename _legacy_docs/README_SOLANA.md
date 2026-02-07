#  OBI WORK: Agentic Liquidity Infrastructure

> **Autonomous trading agents for Solana ecosystems, powered by on-chain access.**

##  Overview
OBI WORK is a hybrid system combining high-frequency trading intelligence (Off-Chain) with decentralized access control (On-Chain Solana). It provides liquidity to key Solana venues (Backpack, and soon Phoenix/Drift) while allowing users to access these capabilities via **OBI Pass** tokens and **Solana Blinks**.

## ️ Architecture

### 1. The Brain (Off-Chain Agents)
Located in `/core` and `/strategies`.
*   **Sniper Executor:** HFT logic for Orderbook Imbalance (OBI) trading.
*   **Aggressive Hunter:** Scans top volume assets and "Alpha Assets" (High Funding).
*   **Risk Manager:** Real-time capital protection and "Golden Equation" logic.

### 2. The Heart (On-Chain Solana)
Located in `/obi_solana_core`.
*   **ObiPass Program (Rust):** Anchor program for issuing Token 2022 access passes.
*   **Solana Gatekeeper:** Python module verifying on-chain ownership to unlock off-chain agents.
*   **Solana Actions (Blinks):** Next.js routes (`/api/actions`) for viral interaction on X (Twitter).

### 3. The Face (Web Interface)
Located in `/obiwork_web`.
*   **Dashboard:** Real-time visualization of agent performance and PnL.
*   **Mint Page:** UI for purchasing OBI Pass licenses.

##  Quick Start

### Running the Agent (Hunter Mode)
```bash
python3 tools/aggressive_hunter.py
```

### Running the Web App (Blinks Support)
```bash
cd obiwork_web
npm run dev
```

### Verifying Access (Gatekeeper)
```python
from obi_solana_core.gatekeeper.solana_gatekeeper import SolanaGatekeeper
# Checks if wallet holds OBI Pass
access = SolanaGatekeeper().check_access("WalletAddr...")
```

##  Colosseum / Solana 2026 Status
*   **Track:** DeFi / AI Infrastructure
*   **Status:** MVP Live & Eligible
*   **Key Tech:** SPL Token 2022, Solana Actions (Blinks), Anchor.

---
*Built for the Solana Renaissance.*
