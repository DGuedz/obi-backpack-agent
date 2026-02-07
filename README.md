# OBI Agent: The Agent-Native Trading Desk
> **"VSC is for agents what SQL is for databases: a minimal, deterministic, and auditable language."**

OBI (Order Book Imbalance) is an **Autonomous Trading Desk** built natively for the Solana ecosystem. It operates on a **Value-Separated Content (VSC)** cognitive runtime, allowing it to execute institutional-grade strategies with zero cognitive latency and full on-chain auditability.

**Built for the Colosseum AI Agent Hackathon.**

---

##  The Agentic Paradigm (VSC)

Most trading bots are fragile scripts wrapped in complex frameworks. OBI is different. It uses **VSC (Value-Separated Content)** as its native language.

### Why VSC?
*   **Zero Latency:** No JSON parsing overhead. Decisions are binary and immediate.
*   **Deterministic:** Rules are strict boolean gates. No "hallucinations".
*   **Auditable:** Every decision logic is a flat file hashable on-chain.

**Example VSC Logic:**
```vsc
project_name,OBI Agent
core_purpose,Autonomous High-Frequency Trading with On-Chain Volume Validation
real_world_problem,Lack of transparency and auditability in algorithmic trading volumes
value_created,Immutable Audit Trail|Real-Time Proof of Volume|Capital Efficiency
```

---

## ️ Proof of Volume (The "Audit Receipt")

OBI introduces a new standard for agent accountability: **The Audit Receipt**.
Instead of trusting a black box, OBI generates a cryptographic receipt of its tokenomics and volume, hashed and signed via AgentWallet on Solana.

###  Battle-Tested Metrics (Backpack Season 4)
This agent is not a simulation. It has been deployed in production, farming volume and reputation under hostile market conditions.

**Global Performance:**
*   **Total Volume:** `$2,272,666.11` (Honored)
*   **Rank:** Level 14 (Gold Tier)
*   **Next Milestone:** Level 15 ($3.2M)

**Asset-Specific Mastery (Volume Depth):**
The agent distributes liquidity intelligently across high-beta and major assets.

| Asset | Volume Tier | Status |
| :--- | :--- | :--- |
| **SOL-PERP** | **Level 14** (>$320k) | 🟢 Honored |
| **BTC-PERP** | **Level 14** (>$320k) | 🟢 Honored |
| **ETH-PERP** | **Level 13** (>$160k) | 🟢 Honored |
| **LIT-PERP** | **Level 13** (>$160k) | 🟢 Honored |
| **HYPE-PERP** | **Level 12** (>$80k) | 🟢 Honored |
| **PAXG/IP/BNB** | **Level 11** (>$40k) | 🟢 Honored |
| **SKR/SUI/APT** | **Level 11** (>$40k) | 🟢 Honored |
| **XRP/FOGO/0G** | **Level 10** (>$20k) | 🟡 Friendly |

*Data updates every 10 minutes via Backpack API.*

**Run the Audit:**
```bash
python3 tools/generate_audit_receipt.py
```

**Output (The Evidence):**
```text
============================================================
       AGENT TOKENOMICS AUDIT RECEIPT (PROOF OF VSC)
============================================================
 Project:      OBI AGENT
 Chain:        Solana (Mainnet)
 VSC Hash:     52ea99d8385e617f... (SHA256)
------------------------------------------------------------
 [FINAL VALIDATION]
 Real Demand:           TRUE
 Survives w/o Hype:     TRUE
 Project Valid:         TRUE
============================================================
```

---

##  Architecture

### 1. Perception Layer (On-Chain & Off-Chain)
- **Whale Wall Detection**: Scans orderbooks for liquidity voids.
- **OBI Analysis**: Real-time imbalance calculation (Buyer vs Seller pressure).
- **AgentWallet Integration**: Signs every critical milestone on-chain.

### 2. Decision Layer (VSC Brain)
- **Prompt Zero**: No conversational fluff. Pure logic execution.
- **Kill Switch**: Hard equity stops enforcing capital preservation.
- **Strategy Selection**: Switches between *Sniper Mode* (Volatility) and *Swing Farm* (Lateral) based on market regime.

### 3. Execution Layer (Backpack Exchange)
- **Maker-First**: Provides liquidity to capture rebates.
- **Atomic Risk Check**: ATR-based sizing per trade.

---

##  Technology Stack

---

##  Agent Dashboard (Web Interface)

OBI includes a specialized Web Interface (Next.js) for monitoring agent performance, visualizing on-chain proofs, and managing licenses.

**Access the Dashboard:**
1. Navigate to the web module:
   ```bash
   cd obiwork_web
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the interface:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:3000` to view the **Agent Control Center**.

---

##  License & Copyright

### Code (Software)
The source code is licensed under the **MIT License**. You are free to fork, modify, and use it, provided you include the original copyright notice.

### Concepts & Documentation (IP)
<a href="https://github.com/doublegreen/backpacktrading">OBI Agent (VSC Protocol)</a> © 2026 by <a href="https://x.com/dg_doublegreen">Diego Guedes Da Silva</a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>

You are free to share and adapt, even commercially, provided you give appropriate credit.

**Copyright (c) 2026 Diego Guedes Da Silva. All Rights Reserved.**


- **Runtime**: Python 3.10+ (Optimized for speed)
- **Cognitive Engine**: VSC (Value-Separated Content)
- **Identity**: AgentWallet (Solana On-Chain Signing)
- **Execution**: Backpack Exchange API
- **Security**: Environment-based key management (Zero hardcoded secrets)

---

##  How to Run

### Prerequisites
1. Python 3.10+
2. Backpack Exchange Account
3. AgentWallet (for on-chain validation)

### Installation

```bash
# Clone the repository
git clone https://github.com/DGuedz/obi-backpack-agent.git
cd obi-backpack-agent

# Install dependencies
pip install -r requirements.txt

# Configure Secrets
cp .env.example .env
# Edit .env with your BACKPACK_API_KEY and AGENT_WALLET credentials
```

### Start the Agent

```bash
python3 start_system.py
```

---

##  Roadmap: The Agentic Future

1.  **On-Chain Inference**: Deploy VSC logic directly to Solana via Cauldron (Frostbite VM).
2.  **DeFi Integration**: Expand execution to Jupiter and Kamino.
3.  **Social Proof**: Auto-publish audit receipts to X/Twitter via API.

---

**Disclaimer**: This software is experimental. Use at your own risk.
