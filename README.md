# OBI: The Autonomous Capital Allocator

> **"Price lies, liquidity doesn't."**

OBI (Order Book Imbalance) is an autonomous hedge fund agent operating on Solana's infrastructure (Backpack Exchange). It analyzes institutional order flow, detects whale manipulation, and allocates capital dynamically to protect retail investors from "smart money" traps.

**Built for the Colosseum AI Agent Hackathon.**

---

##  The Brain (Autonomous Architecture)

OBI is not just a trading bot; it is a self-driving capital manager.

### 1. Perception Layer (Scanner)
- **Whale Wall Detection**: Identifies large bid/ask walls (3x+ size) to detect support/resistance manipulation.
- **OBI Analysis**: Calculates real-time Order Book Imbalance to determine the true direction of institutional flow.
- **Smart Money Tracking**: Filters assets by volume and depth to avoid "pump and dump" schemes.

### 2. Decision Layer (The Brain)
- **Context Awareness**: Checks account equity and health before every cycle.
- **Strategy Selection**:
    - **️ Sniper Mode**: Triggered by high volatility + strong OBI (>0.35). Uses VWAP filtering to enter only with the trend.
    - ** Swing Farm Mode**: Triggered by lateral markets. Allocates micro-sizes to top 3 rising assets to capture spread.
- **Kill Switch**: Hard stop mechanism that terminates all operations if equity drops below safety thresholds.

### 3. Execution Layer (The Farmer)
- **Maker-First Negotiation**: Attempts to provide liquidity (Limit Orders) to capture spread and reduce fees.
- **Taker Aggression**: Switches to market orders only when OBI is extreme (>0.5), signaling an imminent breakout.
- **Atomic Risk Check**: Calculates ATR (Average True Range) before *every* trade to adjust position size dynamically.

---

## ️ Technology Stack

- **Language**: Python 3.10+
- **Infrastructure**: Solana (via Backpack Exchange API)
- **Core Libraries**: `asyncio`, `requests`, `numpy` (minimized dependencies for speed)
- **Security**: Environment-based key management (Zero hardcoded secrets)

---

##  How to Run

### Prerequisites
1. Python 3.10+
2. A Backpack Exchange account (API Key & Secret)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/obi-agent.git
cd obi-agent

# Install dependencies
pip install -r requirements.txt

# Configure Secrets
cp .env.example .env
# Edit .env with your BACKPACK_API_KEY and BACKPACK_API_SECRET
```

### Start the Agent

```bash
python3 agent_brain.py
```

The agent will immediately start scanning the market and printing its decision logic to the console.

---

## ️ Risk Management Protocol

OBI prioritizes **Capital Preservation** over profit.

1.  **VWAP Filter**: Never buys below the daily Volume Weighted Average Price (avoids "catching falling knives").
2.  **RSI Guard**: Prevents selling at the bottom (Oversold) or buying at the top (Overbought).
3.  **Equity Hard Stop**: If the portfolio drops below a critical level (e.g., $2.00), the agent performs an emergency shutdown.

---

##  Future Roadmap

- **LLM Integration**: Feeding OBI metrics into an LLM to generate natural language market reports.
- **DeFi Expansion**: Integrating with Jupiter for on-chain swaps beyond CEXs.
- **Social Layer**: Automatically posting trade rationale to X (Twitter).

---

**Disclaimer**: This software is experimental. Use at your own risk.
