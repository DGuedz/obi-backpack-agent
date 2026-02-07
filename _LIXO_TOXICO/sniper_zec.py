
import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

load_dotenv()

def sniper_zec():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    
    symbol = "ZEC_USDC_PERP"
    price = 368.50
    usdc_amount = 80
    leverage = 5
    
    qty = (usdc_amount * leverage) / price
    qty = round(qty, 1) # ZEC precision? usually 2 or 3 decimals. Let's check min qty.
    # ZEC price ~300. 0.1 ZEC = $30. 1 ZEC = $300.
    # 0.2 ZEC = $60.
    # Let's try 1 decimal place.
    
    print(f" ZEC SNIPER: Armadilha em ${price}...")
    
    try:
        order = trade.execute_order(
            symbol=symbol,
            side="Bid",
            order_type="Limit",
            quantity=str(qty),
            price=str(price),
            post_only=True
        )
        print(f" Ordem Plantada: {order['id']} | {qty} ZEC @ ${price}")
    except Exception as e:
        print(f" Erro: {e}")

if __name__ == "__main__":
    sniper_zec()
