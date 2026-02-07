import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

print("--- SALDO ATUAL ---")
balances = data.get_balances()
usdc = balances.get('USDC', {})
available = usdc.get('available', 0)
locked = usdc.get('locked', 0)

print(f"USDC Disponível: ${available}")
print(f"USDC Em Ordem/Margem: ${locked}")
print(f"Total: ${float(available) + float(locked)}")

print("\n--- POSIÇÕES ABERTAS ---")
positions = data.get_positions()
for p in positions:
    if float(p['netQuantity']) != 0:
        print(f"{p['symbol']}: {p['netQuantity']} (PnL: {p['pnlUnrealized']})")
