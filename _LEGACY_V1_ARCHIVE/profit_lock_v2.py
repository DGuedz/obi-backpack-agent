import time
import os
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

def profit_lock_v2():
    print("\n [PROFIT LOCK V2] TRAILING STOP & BREAKEVEN MANAGER")
    print("    Objective: Secure Profits. Never let a winner turn loser.")
    print("   ️ Config: Breakeven @ 0.2% Profit | Trail Start @ 0.5% Profit")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    # Cache to avoid spamming API with updates
    # Key: Symbol, Value: Last Known Stop Price
    managed_stops = {}
    
    while True:
        try:
            positions = data.get_positions()
            open_orders = data.get_open_orders()
            
            if not positions:
                time.sleep(1)
                continue
                
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
                entry_price = float(pos.get('entryPrice', 0))
                
                if qty == 0 or entry_price == 0: continue
                
                # Get Current Price
                ticker = data.get_ticker(symbol)
                current_price = float(ticker['lastPrice'])
                
                # Calculate PnL % (Unleveraged for logic consistency, or Leveraged? Let's use Price Move %)
                # If Long: (Curr - Entry) / Entry
                # If Short: (Entry - Curr) / Entry
                if qty > 0: # Long
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    side = "Buy"
                    sl_side = "Ask" # Sell to stop
                else: # Short
                    pnl_pct = (entry_price - current_price) / entry_price * 100
                    side = "Sell"
                    sl_side = "Bid" # Buy to stop
                    
                # Identify Existing Stop Loss Order
                current_sl_order = None
                current_sl_price = 0.0
                
                for order in open_orders:
                    if order['symbol'] == symbol and order['side'] == sl_side:
                        # Assuming it's a Stop order (check type or triggerPrice)
                        if 'triggerPrice' in order:
                            current_sl_order = order
                            current_sl_price = float(order['triggerPrice'])
                            break
                            
                # --- LOGIC CORE ---
                
                # 1. BREAKEVEN CHECK (0.2% Profit)
                # Ensure we cover fees (~0.12% round trip taker, or less if maker)
                if pnl_pct > 0.2:
                    target_sl = entry_price # Breakeven
                    
                    # Optimization: Move slightly past entry to cover fees
                    if side == "Buy":
                        target_sl = entry_price * 1.001
                    else:
                        target_sl = entry_price * 0.999
                        
                    # Check if update is needed
                    # For Long: New SL must be HIGHER than current SL
                    # For Short: New SL must be LOWER than current SL
                    update_needed = False
                    
                    if current_sl_price == 0:
                        update_needed = True # No SL exists (Sentinel should have caught this, but we act too)
                    elif side == "Buy" and target_sl > current_sl_price:
                        update_needed = True
                    elif side == "Sell" and target_sl < current_sl_price:
                        update_needed = True
                        
                    if update_needed:
                        print(f"   ️ BREAKEVEN TRIGGER: {symbol} PnL {pnl_pct:.2f}%")
                        _update_stop_loss(trade, symbol, sl_side, abs(qty), target_sl, current_sl_order)
                        continue

                # 2. TRAILING STOP (Start at 0.5% Profit)
                if pnl_pct > 0.5:
                    # Trail Distance: 0.2% away from price
                    trail_dist = 0.2
                    
                    if side == "Buy":
                        target_sl = current_price * (1 - trail_dist/100)
                        # Only update if moving UP
                        if target_sl > current_sl_price:
                            print(f"    TRAILING PROFIT: {symbol} PnL {pnl_pct:.2f}% -> Moving SL to {target_sl:.4f}")
                            _update_stop_loss(trade, symbol, sl_side, abs(qty), target_sl, current_sl_order)
                    
                    else: # Short
                        target_sl = current_price * (1 + trail_dist/100)
                        # Only update if moving DOWN
                        if target_sl < current_sl_price or current_sl_price == 0:
                             print(f"    TRAILING PROFIT: {symbol} PnL {pnl_pct:.2f}% -> Moving SL to {target_sl:.4f}")
                             _update_stop_loss(trade, symbol, sl_side, abs(qty), target_sl, current_sl_order)

            time.sleep(2)
            
        except Exception as e:
            print(f"   ️ Error in Profit Lock: {e}")
            time.sleep(5)

def _update_stop_loss(trade, symbol, side, qty, price, existing_order):
    """
    Cancels existing SL and places new one.
    Atomic-ish: We hope execution is fast.
    """
    try:
        if existing_order:
            print(f"       Cancelling old SL {existing_order.get('id')}...")
            trade.cancel_open_orders(symbol) # Cancel all for symbol (safer to clear clutter)
            
        print(f"       Setting New SL @ {price:.4f}...")
        trade.execute_order(
            symbol=symbol,
            side=side,
            order_type="StopMarket",
            quantity=qty,
            trigger_price=price
        )
        print("       SL Updated.")
    except Exception as e:
        print(f"       Failed to update SL: {e}")

if __name__ == "__main__":
    profit_lock_v2()
