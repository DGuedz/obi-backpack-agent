import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

def fix_avax():
    auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
    trade = BackpackTrade(auth)
    
    symbol = "AVAX_USDC_PERP"
    qty = 1.81 # From log
    
    # Preço aproximado de entrada: 10.9 (SL 11.198 era +~3%, 11.198/1.03 = 10.87)
    entry_price = 10.87
    
    # 3% SL, 7% TP (AWM Strategy)
    sl_pct = 0.03
    tp_pct = 0.07
    
    # Short -> SL acima, TP abaixo
    sl_price = entry_price * (1 + sl_pct)
    tp_price = entry_price * (1 - tp_pct)
    
    # Arredondamento CORRETO para AVAX (>10 USD -> 2 casas)
    sl_price = round(sl_price, 2)
    tp_price = round(tp_price, 2)
    
    print(f" FIXING AVAX PROTECTION (Precision Fix)...")
    print(f"   SL: {sl_price} | TP: {tp_price}")
    
    # 1. Place Stop Loss (Buy/Bid Trigger)
    # OBS: Short position -> Exit is Buy/Bid.
    # No atomic_hunt.py, eu vi "exit_side = Bid" para Short.
    
    print(f"️ Placing SL (Buy) at {sl_price}...")
    trade.execute_order(
        symbol=symbol,
        side="Bid",
        price="0",
        quantity=qty,
        order_type="StopLoss",
        trigger_price=str(sl_price)
    )
    
    # 2. Place Take Profit (Buy/Bid Trigger)
    print(f" Placing TP (Buy) at {tp_price}...")
    trade.execute_order(
        symbol=symbol,
        side="Bid",
        price="0",
        quantity=qty,
        order_type="TakeProfit",
        trigger_price=str(tp_price)
    )

if __name__ == "__main__":
    fix_avax()
