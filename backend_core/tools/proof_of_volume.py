import sys
import os
import datetime
import asyncio
import hashlib
import json
import requests
from dotenv import load_dotenv

# Add paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def publish_onchain(report_hash, volume):
    print("\nINITIATING ON-CHAIN VALIDATION (AGENT WALLET)...")
    
    config_path = os.path.expanduser("~/.agentwallet/config.json")
    if not os.path.exists(config_path):
        print("AgentWallet not configured. Run 'python3 tools/setup_agentwallet.py' first.")
        return

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            
        username = config.get("username")
        api_token = config.get("apiToken")
        
        if not api_token:
            print("Invalid AgentWallet config.")
            return
            
        # Message to Sign
        message = f"OBI_VALIDATION:VOL={volume:.2f}:HASH={report_hash}"
        print(f"Signing Message: {message}")
        
        # Sign Message Endpoint
        url = f"https://agentwallet.mcpay.tech/api/wallets/{username}/actions/sign-message"
        payload = {
            "chain": "solana",
            "message": message
        }
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("success") or data.get("status") == "confirmed":
                print("ON-CHAIN VALIDATION SUCCESS!")
                print(f"   Signature: {data.get('signature', data.get('txHash'))}")
                print(f"   Explorer: {data.get('explorer')}")
            else:
                print(f"Validation Response: {data}")
        else:
            print(f"Validation Failed: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Validation Error: {e}")

def generate_proof_of_volume():
    load_dotenv()
    print("GENERATING PROOF OF VOLUME REPORT (ON-CHAIN/EXCHANGE HISTORY)...")
    print("-" * 60)
    
    transport = BackpackTransport()
    
    try:
        # Try fetching Fills History (Best for Volume)
        limit = 100 
        print(f"Fetching last {limit} filled orders from Backpack API (Fill History)...")
        fills = transport.get_fill_history(limit=limit)
        
        if not fills:
            print("No fill history found.")
            return

        total_volume_usd = 0.0
        total_fees_usd = 0.0
        total_trades = len(fills)
        
        # Analyze fills
        assets_traded = {}
        
        for fill in fills:
            qty = float(fill.get('quantity', 0))
            price = float(fill.get('price', 0))
            fee = float(fill.get('fee', 0))
            symbol = fill.get('symbol', 'Unknown')
            
            # Volume Calculation
            trade_vol = price * qty
            total_volume_usd += trade_vol
            total_fees_usd += fee
            
            # Asset Breakdown
            if symbol not in assets_traded:
                assets_traded[symbol] = {'volume': 0.0, 'trades': 0}
            assets_traded[symbol]['volume'] += trade_vol
            assets_traded[symbol]['trades'] += 1

        # Sort assets by volume
        sorted_assets = sorted(assets_traded.items(), key=lambda x: x[1]['volume'], reverse=True)
        
        # GENERATE MARKDOWN REPORT
        report = f"""# OBI AGENT: Proof of Volume & Real World Validation

**Generated at:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Source:** Backpack Exchange API (Fill History)

## Performance Metrics (Last {limit} Fills Scanned)

| Metric | Value |
| :--- | :--- |
| **Total Volume Generated** | **${total_volume_usd:,.2f} USD** |
| **Total Fills** | **{total_trades}** |
| **Total Fees Paid** | **${total_fees_usd:,.2f} USD** |
| **Average Fill Size** | **${(total_volume_usd/total_trades if total_trades > 0 else 0):,.2f} USD** |

## Top Traded Assets (By Volume)

| Asset | Volume (USD) | Trades |
| :--- | :--- | :--- |
"""
        
        for symbol, data in sorted_assets[:10]: # Top 10
            report += f"| {symbol} | ${data['volume']:,.2f} | {data['trades']} |\n"

        report += """
## Audit Trail (Last 5 Fills)
| Time | Symbol | Side | Price | Quantity | Fee |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
        
        # Add last 5 fills for audit
        for fill in fills[:5]:
            ts = fill.get('timestamp')
            try:
                if str(ts).isdigit():
                    dt_obj = datetime.datetime.fromtimestamp(int(ts)/1000)
                    time_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = str(ts)
            except:
                time_str = str(ts)
                
            report += f"| {time_str} | {fill.get('symbol')} | {fill.get('side').upper()} | ${float(fill.get('price', 0)):,.4f} | {fill.get('quantity')} | ${fill.get('fee')} |\n"

        print(report)
        
        # Save Report
        filename = f"OBI_PROOF_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, "w") as f:
            f.write(report)
        print(f" Report saved to {filename}")

        # Hashing
        report_hash = hashlib.sha256(report.encode('utf-8')).hexdigest()
        print(f" REPORT HASH (SHA256): {report_hash}")
        
        # On-Chain Validation via AgentWallet
        publish_onchain(report_hash, total_volume_usd)

    except Exception as e:
        print(f" Error generating proof: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_proof_of_volume()
