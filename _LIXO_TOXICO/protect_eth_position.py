import os
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

def protect_eth():
    print("️ Iniciando Protocolo de Proteção ETH...")
    
    api_key = os.getenv('BACKPACK_API_KEY')
    private_key = os.getenv('BACKPACK_API_SECRET')
    
    if not api_key:
        print(" API Key missing")
        return

    auth = BackpackAuth(api_key, private_key)
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # 1. Verificar Ordens Abertas
    orders = data.get_open_orders()
    eth_orders = [o for o in orders if o.get('symbol') == 'ETH_USDC_PERP']
    
    has_sl = any(o.get('orderType') in ['StopLimit', 'StopMarket'] and o.get('side') == 'Ask' for o in eth_orders)
    has_tp = any(o.get('orderType') == 'Limit' and o.get('side') == 'Ask' and o.get('reduceOnly') for o in eth_orders)
    
    print(f" Estado Atual: TP={'' if has_tp else ''} | SL={'' if has_sl else ''}")
    
    if not has_sl:
        print("️ Stop Loss ausente! Enviando ordem de proteção...")
        # Stop Loss a 2% abaixo da entrada (~3350 -> 3283)
        # Trigger: 3283. Price: 3280 (Slippage protection)
        
        res = trade.execute_order(
            symbol="ETH_USDC_PERP",
            side="Ask",
            price="3280",
            quantity="0.3",
            order_type="Limit",
            trigger_price="3283",
            reduce_only=True
        )
        if res:
            print(f" Stop Loss Enviado: {res.get('id')}")
        else:
            print(" Falha ao enviar Stop Loss!")
    else:
        print(" Posição ETH já está protegida por Stop Loss.")

if __name__ == "__main__":
    protect_eth()
