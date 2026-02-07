#  Backpack Exchange - Mobile UX Feedback Report (Technical & Power User Perspective)

**User Profile:** High-Frequency Algo-Trader & Mobile Monitor
**Focus Area:** Stability, Precision, and Risk Management on Mobile

---

## 1.  Critical Friction: Memecoin Decimal Input & "Max" Button Logic
**Context:** Recently trading **FOGO_USDC_PERP**, **PEPE**, and **BONK**.
**The Issue:**
The API throws `INVALID_CLIENT_REQUEST: Quantity decimal too long` when standard floating-point calculations are sent for low-value assets. On Mobile, this often manifests as the "Max" button or manual slider generating a number with too many decimals (e.g., `12345.678901` instead of `12345`), causing the "Buy/Sell" button to fail silently or return a generic error.
**Why it hurts UX:**
In high-volatility moments (like the recent -20% FOGO crash), speed is key. Fighting the UI to delete decimal places manually prevents capturing the entry.
**Suggestion:**
Ensure the Mobile UI hard-limits the input field based on the asset's `stepSize` metadata *before* the order is submitted. If `stepSize` is `1` (Integer), the UI keyboard shouldn't even allow a decimal point, or the "Max" calculation should `floor()` the value automatically.

## 2.  The "Ghost Position" Sync Lag
**Context:** High-load moments (Volatility > 10%).
**The Issue:**
After a rapid entry/exit cycle (scalping), the Mobile Wallet/Positions tab often retains a "stale" state. It shows a position as "Open" with frozen PnL, even though it was closed milliseconds ago on the matching engine.
**Why it hurts UX:**
This induces panic. Users (like me) might try to "Panic Close" a position that doesn't exist, leading to an accidental *opening* of an opposite position (Revenge trading against a ghost).
**Suggestion:**
Implement a more aggressive WebSocket subscription for `account.positionUpdate` on the active screen, rather than relying on polling or cached snapshots. Add a visual "Syncing..." indicator or a "Pull to Force Refresh" that actually hits the REST endpoint directly to confirm state.

## 3.  Missing Data: Real-Time Funding Rate Heatmap
**Context:** Trading Perp Contracts (Yield Farming & Squeeze Hunting).
**The Issue:**
The current Mobile UI highlights Price Change (%) well, but hides **Funding Rates** deep inside the pair details. For a Perp-first exchange, Funding is as important as Price.
**Why it hurts UX:**
I cannot scan for "Short Squeeze" candidates (Negative Funding) quickly on mobile. I have to open each pair individually.
**Suggestion:**
Add a "Funding Rate" sort/filter option in the Markets tab, or a small visual indicator (e.g., a colored dot: Red for Negative, Green for Positive) next to the ticker name in the list view. This turns the app into a powerful scanner.

## 4. ️ Feature Request: "Guardian Mode" (Panic Button)
**Context:** Managing risk on the go.
**The Issue:**
Closing multiple positions during a market crash (like the one observed today) requires too many taps: *Tap Asset -> Tap Position -> Tap Close -> Confirm*.
**Why it hurts UX:**
In a crash, every second is slippage.
**Suggestion:**
Add a "Guardian / Emergency" toggle in the Portfolio view. When active, it reveals a "Flatten All" or "Close All PERPS" button. This gives institutional-grade control to mobile retail users.

---
*Submitted by a dedicated Backpack ecosystem developer & trader.*
