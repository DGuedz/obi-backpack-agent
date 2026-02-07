import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

async def fix_btc_protection():
    print("️ APLICANDO PROTEÇÃO DE EMERGÊNCIA EM BTC...")
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    
    symbol = "BTC_USDC_PERP"
    qty = "0.002" # Quantity executed previously
    
    # Corrected Precision (1 decimal for BTC)
    tp_price = "84240.9"
    sl_price = "82581.0"
    
    print(f"   Qty: {qty}")
    print(f"   TP Alvo: {tp_price}")
    print(f"   SL Alvo: {sl_price}")
    
    # TP
    print("    Re-enviando TP...")
    res_tp = trade.execute_order(
        symbol=symbol,
        side="Ask", # Closing Buy
        order_type="TriggerMarket",
        quantity=qty,
        price=None,
        trigger_price=tp_price
    )
    print(f"   TP Status: {res_tp.get('status', 'ERROR') if res_tp else 'ERROR'}")
    
    # SL
    print("   ️ Re-enviando SL...")
    res_sl = trade.execute_order(
        symbol=symbol,
        side="Ask", # Closing Buy
        order_type="TriggerMarket",
        quantity=qty,
        price=None,
        trigger_price=sl_price
    )
    print(f"   SL Status: {res_sl.get('status', 'ERROR') if res_sl else 'ERROR'}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fix_btc_protection())
