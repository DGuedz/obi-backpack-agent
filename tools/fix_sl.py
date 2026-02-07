import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport

def fix_sl():
    print(" FIXING STOP LOSSES...")
    trade = BackpackTransport()
    
    # ETH SL
    # Posição Short (Ask), SL é Compra (Bid) acima do preço
    # Entrada ~2686.2, SL 2739.9
    print("    Fixing ETH SL...")
    sl_eth = trade.execute_order(
        symbol="ETH_USDC_PERP",
        side="Bid",
        order_type="Market", # Tentativa 1: Market com Trigger
        quantity="0.037",
        price=None,
        trigger_price="2739.9"
    )
    if sl_eth:
        print(f"       ETH SL Fixed: {sl_eth.get('id')}")
    else:
        print("       Failed (Market w/ Trigger). Trying 'StopMarket'...")
        # Tentativa 2: StopMarket
        sl_eth_2 = trade.execute_order(
            symbol="ETH_USDC_PERP",
            side="Bid",
            order_type="StopMarket", 
            quantity="0.037",
            price=None,
            trigger_price="2739.9"
        )
        if sl_eth_2:
             print(f"       ETH SL Fixed (StopMarket): {sl_eth_2.get('id')}")

    # SUI SL
    # Entrada ~1.2619, SL 1.2871
    print("    Fixing SUI SL...")
    sl_sui = trade.execute_order(
        symbol="SUI_USDC_PERP",
        side="Bid",
        order_type="Market",
        quantity="79.2",
        price=None,
        trigger_price="1.2871"
    )
    if sl_sui:
        print(f"       SUI SL Fixed: {sl_sui.get('id')}")
    else:
        print("       Failed (Market w/ Trigger). Trying 'StopMarket'...")
        sl_sui_2 = trade.execute_order(
            symbol="SUI_USDC_PERP",
            side="Bid",
            order_type="StopMarket",
            quantity="79.2",
            price=None,
            trigger_price="1.2871"
        )
        if sl_sui_2:
             print(f"       SUI SL Fixed (StopMarket): {sl_sui_2.get('id')}")

if __name__ == "__main__":
    fix_sl()
