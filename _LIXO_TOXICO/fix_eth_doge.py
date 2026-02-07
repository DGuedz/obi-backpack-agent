import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

def fix_positions():
    print(" FIXING MISSING TPs (ETH & DOGE)")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    positions = data.get_positions()
    
    # 1. ETH_USDC_PERP (Short)
    eth_pos = next((p for p in positions if p['symbol'] == "ETH_USDC_PERP" and float(p['netQuantity']) != 0), None)
    if eth_pos:
        qty = abs(float(eth_pos['netQuantity']))
        entry = float(eth_pos['entryPrice'])
        tp_price = round(entry * (1 - 0.007), 2) # 0.7% Target
        print(f"ETH Short {qty} @ {entry} -> Adding TP @ {tp_price}")
        
        try:
            trade.execute_order(
                symbol="ETH_USDC_PERP",
                side="Bid", # Buy to Cover
                order_type="Limit",
                quantity=str(qty),
                price=str(tp_price)
            )
            print(" ETH TP Sent.")
        except Exception as e:
            print(f" ETH Error: {e}")
            
    # 2. DOGE_USDC_PERP (Long)
    doge_pos = next((p for p in positions if p['symbol'] == "DOGE_USDC_PERP" and float(p['netQuantity']) != 0), None)
    if doge_pos:
        qty = abs(float(doge_pos['netQuantity']))
        entry = float(doge_pos['entryPrice'])
        tp_price = round(entry * (1 + 0.007), 5) # 0.7% Target (5 decimals for DOGE)
        print(f"DOGE Long {qty} @ {entry} -> Adding TP @ {tp_price}")
        
        try:
            trade.execute_order(
                symbol="DOGE_USDC_PERP",
                side="Ask", # Sell to Close
                order_type="Limit",
                quantity=str(qty),
                price=str(tp_price)
            )
            print(" DOGE TP Sent.")
        except Exception as e:
            print(f" DOGE Error: {e}")

if __name__ == "__main__":
    fix_positions()
