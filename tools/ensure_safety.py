import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from core.backpack_transport import BackpackTransport

async def ensure_safety():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    transport = BackpackTransport()
    
    print("️ ENSURING SAFETY SHIELDS...")
    
    # 1. Get Positions
    positions = transport.get_positions()
    active_symbols = []
    if positions:
        for p in positions:
            if float(p.get('netQuantity', 0)) != 0:
                active_symbols.append(p)
    
    if not active_symbols:
        print("    No active positions to protect.")
        return

    # 2. Get Open Orders
    orders = transport.get_open_orders()
    protected_symbols = set()
    if orders:
        for o in orders:
            protected_symbols.add(o['symbol'])
            
    # 3. Apply Missing Shields
    for p in active_symbols:
        symbol = p['symbol']
        # Derive side from quantity
        qty = float(p.get('netQuantity', 0))
        entry_price = float(p.get('entryPrice', 0))
        
        is_long = qty > 0
        current_side = "Buy" if is_long else "Sell"
        
        if symbol not in protected_symbols:
            print(f"   ️ UNPROTECTED POSITION DETECTED: {symbol} ({current_side})")
            
            # Calculate SL (1.5%)
            sl_pct = 0.015
            if is_long:
                sl_price = entry_price * (1 - sl_pct)
                exit_side = "Ask"
            else:
                sl_price = entry_price * (1 + sl_pct)
                exit_side = "Bid"
            
            # Heuristic Rounding
            if sl_price > 1000:
                final_sl = round(sl_price, 1)
            elif sl_price > 10:
                final_sl = round(sl_price, 2)
            elif sl_price > 1:
                final_sl = round(sl_price, 3)
            else:
                final_sl = round(sl_price, 4)
            
            # Execute Stop Loss
            try:
                print(f"   ️ Deploying Shield for {symbol} @ {final_sl}...")
                trade.execute_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="StopLoss",
                    quantity=str(abs(qty)),
                    price="0",
                    trigger_price=str(final_sl)
                )
                print("    Shield Deployed.")
            except Exception as e:
                print(f"    Failed to deploy shield: {e}")
        else:
            print(f"    {symbol} is already protected.")

if __name__ == "__main__":
    asyncio.run(ensure_safety())
