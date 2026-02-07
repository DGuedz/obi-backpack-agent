import os
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
trade = BackpackTrade(auth)

symbol = "ETH_USDC_PERP"

print(f"Cancelando ordens em {symbol}...")
trade.cancel_all_orders(symbol)

print("Zerando Posição (Market Buy 0.05)...")
trade.execute_order(symbol, "Bid", "Market", 0.05, "Market", reduce_only=True)

print("Concluído.")
