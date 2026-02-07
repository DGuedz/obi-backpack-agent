#!/usr/bin/env python3
"""
 BONK SNIPER - ENTRADA CIRÚRGICA ($50)
Entra em kBONK_USDC_PERP com $50 (Maker Only) para garantir sustentabilidade.
Foco: Farmar taxas e aproveitar o repique.
"""

import os
import time
import math
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

# Configuração
SYMBOL = "kBONK_USDC_PERP"
SIZE_USDC = 50.0  # $50 (Conforme solicitado)
LEVERAGE = 5      # 5x (Padrão de segurança)

def run_bonk_sniper():
    print(f" INICIANDO BONK SNIPER ({SYMBOL})...")
    print(f"    Tamanho: ${SIZE_USDC} | Alavancagem: {LEVERAGE}x")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # 1. Cancelar Ordens Antigas em BONK
    try:
        trade.cancel_open_orders(SYMBOL)
        print(f"    Ordens antigas canceladas.")
    except:
        pass
        
    time.sleep(1) 
    
    try:
        # 2. Obter Preço e Calcular Qtd
        ticker = data.get_ticker(SYMBOL)
        last_price = float(ticker['lastPrice'])
        
        # Correção Crítica para BONK: A quantidade deve respeitar o stepSize.
        # Geralmente kBONK aceita apenas inteiros ou decimais específicos.
        # Erro anterior: "Quantity decimal too long" mesmo com int(). 
        # Pode ser que int() vire "4810" string e a API aceite, mas se passar 4810.0 falha.
        # Vamos garantir string sem decimal.
        
        qty_float = SIZE_USDC / last_price
        
        # Correção Crítica BASEADA NO STEPSIZE (100.0)
        # O stepSize é 100. Isso significa que a quantidade DEVE ser múltiplo de 100.
        # Ex: 4800 (OK), 4810 (ERRO).
        
        step_size = 100
        qty = int(qty_float / step_size) * step_size # Arredonda para baixo para o múltiplo de 100 mais próximo
        qty_str = str(qty)
        
        print(f"    Preço Atual: ${last_price} | Qtd Alvo Ajustada (Step 100): {qty_str}")
        
        # 3. Executar Ordem Maker (Post Only)
        price = last_price * 0.998 # 0.2% abaixo
        price = round(price, 6)
        
        print(f"    Tentando Limit Buy em ${price} (Maker Only)...")
        
        payload = {
            "symbol": SYMBOL,
            "side": "Bid",
            "orderType": "Limit",
            "quantity": qty_str,
            "price": str(price),
            "postOnly": True,
            "selfTradePrevention": "RejectTaker"
        }
        
        # Chamada direta via requests para garantir payload limpo se a classe trade estiver convertendo errado
        import requests
        headers = auth.get_headers(instruction="orderExecute", params=payload)
        url = "https://api.backpack.exchange/api/v1/order"
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            order = response.json()
            print(f"      Ordem Criada! ID: {order.get('id')} @ ${price}")
        else:
             print(f"      Erro API: {response.text}")
             # Fallback: Tentar via classe trade normal
             order = trade.execute_order(SYMBOL, "Bid", price, qty, "Limit", post_only=True)

        
        if order:
            print(f"      Ordem Criada! ID: {order.get('id')} @ ${price}")
        else:
            print(f"     ️ Post Only rejeitou (Preço moveu). Tentando 0.1% abaixo...")
            # Tentativa 2: 0.1% abaixo para garantir Maker
            price = price * 0.999
            price = round(price, 6) # Ajuste de precisão
            
            order = trade.execute_order(
                symbol=SYMBOL,
                side="Bid",
                price=price,
                quantity=qty,
                order_type="Limit",
                post_only=True
            )
            
            if order:
                 print(f"      Ordem Ajustada Criada! ID: {order.get('id')} @ ${price}")
            else:
                 print(f"      Falha ao criar ordem em BONK.")

        # 4. Configurar Proteção Imediata (Se a ordem pegar, o Risk Manager pega depois, 
        # mas podemos tentar deixar o SL/TP engatilhado se a API suportasse OCO, mas Backpack não suporta nativo fácil assim)
        print("   ️ ATENÇÃO: Execute o 'risk_manager.py' assim que a ordem for preenchida!")

    except Exception as e:
        print(f"    Erro Fatal: {e}")

    print("\n BONK SNIPER CONCLUÍDO.")

if __name__ == "__main__":
    run_bonk_sniper()
