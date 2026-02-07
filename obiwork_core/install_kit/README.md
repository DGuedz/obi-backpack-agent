# OBI CORE - LOCAL INSTALLATION GUIDE

This kit allows you to install the **OBI Operating System (Core)** on your local machine using Trae IDE, Cursor, or VS Code.

##  Quick Start

### Option 1: Via Terminal (Mac/Linux)
1. Open the integrated terminal in your IDE.
2. Navigate to this folder:
   ```bash
   cd obiwork_core/install_kit
   ```
3. Run the installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

### Option 2: Manual Setup
1. Create a virtual environment:
   ```bash
   python3 -m venv obi_env
   ```
2. Activate it:
   ```bash
   source obi_env/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install requests pandas ccxt termcolor
   ```

## ️ Available Tools

Once installed, you can run the OBI tools from the root directory:

**1. Wallet Tracker (Spyglass)**
Track allies and monitor activity.
```bash
python3 obiwork_core/gatekeeper/wallet_tracker.py --track <WALLET_ADDRESS> --label "Ally Name"
```

**2. Compliance Gate (Shield)**
Audit tokens and wallets for risks.
```bash
python3 obiwork_core/gatekeeper/compliance_gate.py --scan <WALLET_ADDRESS>
```

##  Dashboard Connection
Your local OBI instance can be connected to the web dashboard. Ensure you have the `obiwork_web` server running locally (`npm run dev`) to access the visual interface at `http://localhost:3000`.
