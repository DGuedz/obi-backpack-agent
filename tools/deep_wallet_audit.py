import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport

def deep_audit():
    print("️ DEEP WALLET AUDIT: Hunting for $100.13...")
    
    transport = BackpackTransport()
    
    # 1. Check Futures Collateral (USDC)
    print("\n1️⃣  FUTURES WALLET CHECK (/api/v1/capital):")
    try:
        capital = transport.get_account_collateral()
        print(f"   Raw Data: {json.dumps(capital, indent=2)}")
        if capital and 'USDC' in capital:
            usdc = capital['USDC']
            avail = float(usdc.get('availableToTrade', 0))
            locked = float(usdc.get('locked', 0))
            print(f"    USDC AVAILABLE: {avail}")
            print(f"    USDC LOCKED: {locked}")
            if avail + locked > 0:
                print("    FUNDS FOUND IN FUTURES!")
        else:
            print("    No USDC in Futures Capital.")
    except Exception as e:
        print(f"    Error checking Futures: {e}")

    # 2. Check Spot Assets (Maybe they are in Spot?)
    print("\n2️⃣  SPOT WALLET CHECK (/api/v1/assets):")
    try:
        assets = transport.get_assets()
        # Assets is list or dict?
        found_any = False
        if isinstance(assets, list):
            for asset in assets:
                sym = asset.get('symbol')
                bal = float(asset.get('balance', 0))
                avail = float(asset.get('available', 0))
                locked = float(asset.get('locked', 0))
                total = bal + avail + locked # Sometimes fields differ
                if total > 0:
                    print(f"    {sym}: {total} (Avail: {avail})")
                    found_any = True
        elif isinstance(assets, dict):
            for sym, data in assets.items():
                 avail = float(data.get('available', 0))
                 if avail > 0:
                     print(f"    {sym}: {avail}")
                     found_any = True
                     
        if not found_any:
            print("    Spot Wallet is EMPTY.")
    except Exception as e:
        print(f"    Error checking Spot: {e}")
        
    # 3. Check Positions (Maybe funds are 100% used in margin?)
    print("\n3️⃣  ACTIVE POSITIONS CHECK:")
    try:
        positions = transport.get_positions()
        if positions:
            print(f"    FOUND {len(positions)} POSITIONS:")
            for pos in positions:
                sym = pos.get('symbol')
                side = pos.get('side')
                pnl = pos.get('pnl', 0)
                margin = pos.get('initialMargin', 0)
                print(f"      -> {sym} {side} | Margin: {margin} | PnL: {pnl}")
        else:
            print("    No Active Positions.")
    except Exception as e:
        print(f"    Error checking Positions: {e}")

    # 4. Check Account Identity (Who am I?)
    print("\n4️⃣  ACCOUNT IDENTITY CHECK (/api/v1/account):")
    try:
        # We need to manually invoke this endpoint as transport doesn't have it
        response = transport._send_request("GET", "/api/v1/account", "accountQuery")
        print(f"   Raw Data: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"    Error checking Identity: {e}")

if __name__ == "__main__":
    deep_audit()
