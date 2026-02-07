# ️ OBI WORK: Colosseum Submission Pitch

## Project Name
**OBI WORK: Agentic Liquidity Infrastructure**

## Tagline
**Providing 24/7 intelligent liquidity to Solana venues via autonomous AI agents, accessible via Solana Blinks.**

## Problem
Liquidity on Solana is growing, but it remains fragmented and dependent on centralized market makers or manual retail trading.
1.  **Liquidity Gaps:** Venues like Backpack often have liquidity voids during off-peak hours.
2.  **Complexity Barrier:** Retail users cannot run 24/7 strategies without complex VPS setups.
3.  **Disconnected Experience:** Alpha is shared on Twitter, but execution happens on disconnected CEX/DEX interfaces.

## Solution
OBI WORK is an **Agentic Liquidity Layer** that bridges high-frequency off-chain execution with on-chain access control.
1.  **Autonomous Agents:** Python-based agents (Sniper/Hunter) run 24/7, providing liquidity (Maker) and correcting inefficiencies (Funding/Spread).
2.  **Tokenized Access (OBI Pass):** Access to these agents is gated by a **Solana Token 2022 (SPL)**. Owning the token in your wallet unlocks the "Worker" off-chain.
3.  **Viral Execution (Blinks):** Users can mint access passes or copy-trade agent signals directly from their Twitter timeline using **Solana Actions**.

## Technical Architecture (The Hybrid Model)
*   **Off-Chain Brain (Python):** HFT execution engine running on Backpack (CEX) and future DEX integrations. Handles Orderbook Imbalance (OBI) analysis and risk management.
*   **Spec-Driven Engineering (SDD):** Built using **Contract-First** methodology. Events defined via **AsyncAPI** (for HFT data streams) and Interfaces via **OpenAPI** (for Blinks), ensuring "Iron Dome" safety protocols are baked into the design.
*   **Capital Efficiency Engine:** Leverages Backpack's **Unified Collateral** to generate passive yield on idle assets (USDC Lending) while simultaneously using them as margin for active trading.
*   **On-Chain Heart (Rust/Anchor):** `ObiPass` program manages license issuance and validation using Token 2022 extensions.
*   **Integration Layer (Blinks):** Next.js API routes (`/api/actions`) serving Solana Actions for frictionless onboarding.

## Traction / Metrics
*   **Volume:** Processing ~$100k daily volume in production (Backpack Exchange).
*   **Efficiency:** Maker-centric strategy achieving near-zero fee costs.
*   **Live:** Web Dashboard and Agent Core active.

## Future Roadmap (Hackathon Goals)
1.  **Fully Decentralize Access:** Move 100% of license revenue to an on-chain Treasury.
2.  **Expand Venues:** Deploy agents to Phoenix and Drift (DEXs).
3.  **Social Trading:** Enable "Copy-Blink" – copy an agent's trade with one click on X.
