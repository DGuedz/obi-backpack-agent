
import os
import sys
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from scalp_ip import IPScalper # Reuse Guardian Logic

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)
trade = BackpackTrade(auth)

def manual_entry_now():
    symbol = "IP_USDC_PERP"
    print(f" MANUAL OVERRIDE: ENTERING {symbol} NOW (LIMIT) ")
    
    # 1. Get Price
    ticker = data.get_ticker(symbol)
    if not ticker:
        print(" Failed to get ticker.")
        return
        
    price = float(ticker['lastPrice'])
    print(f"    Current Price: {price}")
    
    # 2. Determine Side (Based on user context "curto prazo em queda")
    # User said "operar no curto prazo enquanto o preco esta em queda" -> SHORT
    side = 'Sell' # Short
    
    # 3. Calculate Qty (100 USD * 10x)
    leverage = 10
    quantity_usd = 100
    qty = round((quantity_usd * leverage) / price, 1)
    
    print(f"   TARGET: {side} {qty} @ {price} (Leverage {leverage}x)")
    
    # 4. Execute Limit Order (Aggressive Maker)
    # To enter NOW but Limit, we place at Bid (if Selling) or slightly below Ask?
    # Actually, if we want to fill NOW but be Maker, we place at Best Bid.
    # But if price moves, we might miss.
    # User said "Limit".
    limit_price = price # Use current last price
    
    # Re-use IPScalper for execution to get Guardian Protocol
    bot = IPScalper()
    bot.quantity_usd = quantity_usd
    bot.leverage = leverage
    
    # Execute via Bot logic to ensure TP/SL
    print("    Sending Order via Guardian Protocol...")
    # Calculate TP Target (Mid Band is dynamic, pass None to let bot calculate based on pct)
    bot.execute_trade(side, limit_price, None) 

if __name__ == "__main__":
    manual_entry_now()
