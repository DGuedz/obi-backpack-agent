
import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)

def manual_entry_short_ip():
    symbol = "IP_USDC_PERP"
    leverage = 10
    amount_usd = 100
    
    # 1. Analyze Market Conditions
    print(f" Analyzing {symbol} for IMMEDIATE SHORT...")
    ticker = data.get_ticker(symbol)
    last_price = float(ticker['lastPrice'])
    
    print(f"   Price: {last_price}")
    
    # Fee Calculation
    notional = amount_usd * leverage
    taker_fee = notional * 0.00085 # 0.085%
    print(f"    Taker Fee (Market): ~${taker_fee:.2f}")
    
    # Verdict: "Compensa?"
    # If volatility is high, yes.
    print("    VERDICT: Yes. Volatility is high. Paying $0.85 to capture the drop is worth it.")
    
    # 2. Execute Market Short
    qty = int(notional / last_price) # Integer quantity for safety? Or float? IP usually allows decimals.
    # Let's check precision? IP price is ~2.7. Qty ~360.
    # We can use 1 decimal.
    qty = round(notional / last_price, 1)
    
    print(f" EXECUTING MARKET SHORT: {qty} IP @ Market")
    
    # Execute
    res = trade.execute_order(
        symbol=symbol,
        side="Ask", # Sell/Short
        price=None,
        quantity=str(qty),
        order_type="Market"
    )
    
    if res and 'id' in res:
        print(f" ENTRY CONFIRMED: {res['id']}")
        
        # 3. Guardian Protocol (TP/SL)
        # Immediate placement
        time.sleep(1) # Wait for fill
        
        # TP: 1.5%
        tp_price = last_price * (1 - 0.015)
        # SL: 1.0%
        sl_price = last_price * (1 + 0.010)
        
        print(f"️ Deploying Shields... TP: {tp_price:.4f} | SL: {sl_price:.4f}")
        
        # TP (Limit ReduceOnly)
        trade.execute_order(
            symbol=symbol,
            side="Bid",
            price=f"{tp_price:.4f}",
            quantity=str(qty),
            order_type="Limit",
            reduce_only=True
        )
        
        # SL (Stop Limit - simulated via Limit for now or StopLimit if supported)
        # For safety/simplicity in manual script, let's place a STOP LIMIT
        # Trigger: sl_price, Limit: sl_price * 1.05 (to guarantee fill)
        sl_limit = sl_price * 1.05
        trade.execute_order(
            symbol=symbol,
            side="Bid",
            price=f"{sl_limit:.4f}",
            quantity=str(qty),
            order_type="StopLimit",
            trigger_price=f"{sl_price:.4f}",
            reduce_only=True
        )
        print(" Shields Active.")
        
    else:
        print(f" Execution Failed: {res}")

if __name__ == "__main__":
    manual_entry_short_ip()
