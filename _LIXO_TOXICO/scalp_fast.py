import os
import time
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# Load Environment
load_dotenv()

# Configuration
SYMBOL = "FOGO_USDC_PERP"
LEVERAGE = 10
MARGIN_AMOUNT = 50  # $50 Margin
STOP_LOSS_PCT = 0.02  # 2%
TAKE_PROFIT_PCT = 0.04  # 4%

def main():
    print(f" SCALP FAST INITIATED: {SYMBOL}")
    
    # 1. Auth
    api_key = os.getenv('BACKPACK_API_KEY')
    api_secret = os.getenv('BACKPACK_API_SECRET')
    
    if not api_key or not api_secret:
        print(" Error: API Keys not found in environment.")
        return

    auth = BackpackAuth(api_key, api_secret)
    data = BackpackData(auth)
    trade = BackpackTrade(auth)

    # 2. Market Data
    print(" Fetching Market Data...")
    try:
        ticker = data.get_ticker(SYMBOL)
        # print(f"DEBUG Ticker: {ticker}") 
        
        # Fallback if bestBid missing in ticker
        if 'bestBid' not in ticker:
            print("️ 'bestBid' not found in Ticker. Fetching Depth...")
            depth = data.get_orderbook_depth(SYMBOL)
            if depth and depth['bids'] and len(depth['bids']) > 0:
                best_bid = float(depth['bids'][0][0])
                best_ask = float(depth['asks'][0][0])
                mark_price = (best_bid + best_ask) / 2
            else:
                print(" Error: Depth Empty.")
                return
        else:
            best_bid = float(ticker['bestBid'])
            best_ask = float(ticker['bestAsk'])
            mark_price = float(ticker['lastPrice'])
        
        print(f"   Current Price: {mark_price}")
        print(f"   Best Bid: {best_bid} | Best Ask: {best_ask}")
    except Exception as e:
        print(f" Error fetching ticker/depth: {e}")
        return

    # 3. Calculate Quantity
    # Notional Value = Margin * Leverage
    # Quantity = Notional / Price
    notional_value = MARGIN_AMOUNT * LEVERAGE
    quantity = int(notional_value / best_bid)
    
    # Apply Step Size (10 for FOGO)
    step_size = 10
    quantity = (quantity // step_size) * step_size
    
    print(f"   Target Notional: ${notional_value}")
    print(f"   Quantity: {quantity} {SYMBOL} (Step: {step_size})")

    if quantity <= 0:
        print(" Error: Quantity calculated is 0.")
        return

    # 4. Place Limit Order
    print(f" Placing LIMIT BUY Order at {best_bid}...")
    try:
        order = trade.execute_order(
            symbol=SYMBOL,
            side="Bid",
            order_type="Limit",
            quantity=str(quantity),
            price=str(best_bid),
            post_only=True
        )
        print(f" Order Placed: {order.get('id', 'Unknown ID')}")
    except Exception as e:
        print(f" Error placing order: {e}")
        # Retry without PostOnly if it failed? No, discipline.
        return

    # 5. Monitor Execution
    print(" Monitoring Order Status...")
    order_id = order.get('id')
    if not order_id:
        print(" No Order ID returned.")
        return

    filled = False
    fill_price = 0.0

    while not filled:
        try:
            status = data.get_open_orders()
            # Check if our order is still in open orders
            my_order = next((o for o in status if o['id'] == order_id), None)
            
            if my_order:
                print(f"   ... Order Open. Price: {my_order.get('price')} (Current Bid: {best_bid})")
                time.sleep(2)
                # Optional: Cancel and Replace if price moves away? 
                # For now, let's wait.
            else:
                # Order not in open orders -> Filled or Canceled
                print("   Order missing from Open Orders. Checking Fill...")
                # Assuming filled for now, ideally check history
                filled = True
                fill_price = best_bid # Approximation, strictly should fetch fill price
                print(" Order FILLED (or Canceled). Proceeding to Protection.")
                break
        except Exception as e:
            print(f"️ Error checking status: {e}")
            time.sleep(2)

    # 6. Place Protection (Guardian Protocol)
    if filled:
        sl_price = fill_price * (1 - STOP_LOSS_PCT)
        tp_price = fill_price * (1 + TAKE_PROFIT_PCT)
        
        # Round logic (Backpack usually requires specific tick size, doing simple round for now)
        # Assuming 4 decimals for FOGO based on 0.0296 price
        sl_price = round(sl_price, 5)
        tp_price = round(tp_price, 5)

        print(f"️ Placing PROTECTION:")
        print(f"   SL: {sl_price} (-{STOP_LOSS_PCT*100}%)")
        print(f"   TP: {tp_price} (+{TAKE_PROFIT_PCT*100}%)")

        try:
            # Stop Loss (Stop Market for guaranteed exit)
            sl_order = trade.execute_order(
                symbol=SYMBOL,
                side="Ask",
                order_type="Market", 
                quantity=str(quantity),
                price=None,
                trigger_price=str(sl_price)
            )
            print(f"    SL Placed: {sl_order.get('id')}")
        except Exception as e:
            print(f"    SL FAILED: {e}")
            print("   ️ EMERGENCY: CLOSE POSITION MANUALLY!")

        try:
            # Take Profit (Limit Order sitting in book)
            tp_order = trade.execute_order(
                symbol=SYMBOL,
                side="Ask",
                order_type="Limit",
                quantity=str(quantity),
                price=str(tp_price)
            )
            print(f"    TP Placed: {tp_order.get('id')}")
        except Exception as e:
            print(f"    TP FAILED: {e}")

if __name__ == "__main__":
    main()
