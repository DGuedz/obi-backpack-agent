import sys
import os

# Adjust path to include parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obi_work_core.backpack_client import BackpackClient

def check_balance():
    print("🔎 CHECKING OBI03 BALANCES...")
    client = BackpackClient()
    balances = client.get_balances()
    
    if not balances:
        print("❌ FAILED TO FETCH BALANCES.")
        return

    print(f"{'ASSET':<10} {'AVAILABLE':<15} {'LOCKED':<15} {'VALUE (USD)':<15}")
    print("-" * 60)
    
    total_usd = 0.0
    
    for asset, data in balances.items():
        avail = float(data.get('available', 0))
        locked = float(data.get('locked', 0))
        total = avail + locked
        
        if total > 0:
            # Estimate USD Value
            price = 1.0
            if asset != 'USDC':
                ticker = client.get_ticker(f"{asset}_USDC")
                price = float(ticker.get('lastPrice', 0)) if ticker else 0.0
            
            value_usd = total * price
            total_usd += value_usd
            
            print(f"{asset:<10} {avail:<15.6f} {locked:<15.6f} ${value_usd:<15.2f}")

    print("-" * 60)
    print(f"💰 TOTAL ESTIMATED VALUE (SPOT): ${total_usd:.2f}")
    
    print("\n🔎 CHECKING FUTURES COLLATERAL...")
    collateral = client.get_futures_collateral()
    if collateral:
        # Example format: {'balance': '100.00', 'available': '90.00', 'currency': 'USDC'}
        # Or list of assets? Usually USDC only for Backpack Futures currently?
        # Let's inspect raw first or iterate if dict
        print(f"RAW COLLATERAL: {collateral}")
    else:
        print("❌ NO FUTURES COLLATERAL FOUND.")

if __name__ == "__main__":
    check_balance()
