
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.backpack_transport import BackpackTransport

def check_account(name, key, secret):
    print(f"\n DIAGNOSTICANDO CONTA: {name}")
    if not key or not secret:
        print(" Chaves não encontradas.")
        return

    transport = BackpackTransport(api_key=key, api_secret=secret)
    
    # 1. Get Capital (Futures Collateral)
    print("\n FUTURES COLLATERAL (/api/v1/capital):")
    capital = transport.get_account_collateral()
    print(json.dumps(capital, indent=2))
    
    # 2. Get Spot Assets
    print("\n SPOT ASSETS (/api/v1/assets):")
    assets = transport.get_assets()
    print(json.dumps(assets, indent=2))
    
    # 3. Get Positions to check unrealized PnL
    positions = transport.get_positions()
    print("\n POSIÇÕES ABERTAS:")
    print(json.dumps(positions, indent=2))
    
    total_equity = 0
    usdc_balance = 0
    
    # Check Futures Collateral
    if capital:
        for asset, data in capital.items():
            available = float(data.get('available', 0))
            locked = float(data.get('locked', 0))
            staked = float(data.get('staked', 0))
            total = available + locked + staked
            if total > 0:
                print(f"   -> [FUTURES] {asset}: {total} (Avail: {available})")
                if asset in ['USDC', 'USDT']:
                    total_equity += total
                    if asset == 'USDC': usdc_balance += available

    # Check Spot Assets
    if assets:
        # Check if assets is a list (Backpack usually returns a list of objects for assets)
        if isinstance(assets, list):
            for asset_data in assets:
                # asset_data structure: {'symbol': 'USDC', 'balance': '100.13', 'available': '100.13', 'locked': '0', ...}
                # OR {'symbol': 'USDC', 'amount': '100.13', ...}
                # Let's inspect the structure from previous output dump if possible, or handle common cases
                
                symbol = asset_data.get('symbol')
                available = float(asset_data.get('available', 0))
                locked = float(asset_data.get('locked', 0))
                staked = float(asset_data.get('staked', 0))
                total = available + locked + staked
                
                # Some API versions might use 'balance' instead of available/locked sum
                if total == 0 and 'balance' in asset_data:
                    total = float(asset_data.get('balance', 0))
                    
                if total > 0:
                    print(f"   -> [SPOT] {symbol}: {total} (Avail: {available})")
                    if symbol in ['USDC', 'USDT']:
                        total_equity += total
                        
        elif isinstance(assets, dict):
            for asset, data in assets.items():
                available = float(data.get('available', 0))
                locked = float(data.get('locked', 0))
                staked = float(data.get('staked', 0))
                total = available + locked + staked
                if total > 0:
                    print(f"   -> [SPOT] {asset}: {total} (Avail: {available})")
                    if asset in ['USDC', 'USDT']:
                        total_equity += total

    print(f"\n EQUITY TOTAL DETECTADO: ${total_equity:.2f}")
    print(f" USDC DISPONÍVEL (Futures): ${usdc_balance:.2f}")
    return usdc_balance

def check_balance_details():
    # Check Main
    check_account("MAIN (Institucional)", os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    
    # Check LFG
    check_account("LFG (Degen)", os.getenv('BACKPACK_API_KEY_LFG'), os.getenv('BACKPACK_API_SECRET_LFG'))

if __name__ == "__main__":
    check_balance_details()
