#  THE CONSTITUTION (OBI WORK)

## 1. Non-Negotiable Risk Protocols ("Iron Dome")
*   **Capital Preservation:** The Agent MUST NEVER open a position if daily drawdown exceeds 3%.
*   **Stop Loss Mandatory:** Every `open_order` call MUST be atomic and include a `stopLossTriggerPrice`. Orders without SL are rejected locally.
*   **Shadow Guard:** If WebSocket latency > 2000ms, the system MUST trigger `Emergency Drain` (Cancel All + Close Positions).

## 2. On-Chain Sovereignty
*   **ObiPass Validation:** Access to the `AggressiveHunter` core is strictly gated by the `ObiPass` (Token-2022) balance in the user's wallet.
*   **Treasury Flow:** 100% of license revenue MUST flow to the on-chain Treasury contract. No middleman wallets.

## 3. Engineering Standards (SDD)
*   **Contract-First:** All external interfaces (Blinks, HFT Streams) MUST be defined in `openapi.yaml` or `asyncapi.yaml` BEFORE implementation.
*   **Drift Detection:** CI/CD pipelines MUST fail if implementation diverges from the specifications.
*   **Credential Segregation:** Private keys and seeds MUST NEVER be hardcoded. They are injected strictly via ephemeral environment variables.

## 4. Operational Doctrine
*   **No Black Boxes:** Every trade decision (Signal -> Entry) MUST be logged with its rationale (e.g., "Trend Surfer Long: OBI > 0.3").
*   **User Command:** The user's "Manual Exit" command overrides ANY algorithmic signal immediately.
