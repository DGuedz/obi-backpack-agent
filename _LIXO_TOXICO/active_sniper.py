#!/usr/bin/env python3
"""
 ACTIVE SNIPER - AJUSTE DINÂMICO (CORRIGIDO)
Ajusta as ordens para o preço de mercado (Last Price) com proteção Maker.
Foco: ETH e WIF (RSI < 30) e SOL (Reação).
"""

import os
import time
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

# Configuração
SIZE_USDC = 20.0  # $20 por operação
LEVERAGE = 5      # 5x

def run_active_sniper():
    print(" INICIANDO ACTIVE SNIPER (REVISADO)...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # 1. Cancelar Ordens Antigas
    print("️  Cancelando todas as ordens abertas para reposicionar...")
    TARGETS = ['SOL_USDC_PERP', 'ETH_USDC_PERP', 'WIF_USDC_PERP', 'kBONK_USDC_PERP'] 
    for s in TARGETS:
        try:
            trade.cancel_open_orders(s)
            print(f"    Cancelado: {s}")
        except:
            pass
        
    time.sleep(2) # Esperar propagação
    
    print("\n POSICIONANDO NOVAS ORDENS (LAST PRICE MAKER)...")
    
    for symbol in TARGETS:
        try:
            # Pegar Last Price confiável
            ticker = data.get_ticker(symbol)
            last_price = float(ticker['lastPrice'])
            
            # Tentar pegar no preço atual (Se o mercado subiu, isso vira Limit Maker abaixo do preço -> Aceito)
            # Se o mercado caiu, isso vira Taker -> Post Only rejeita.
            # Então começamos com Last Price.
            price = last_price
            
            # Ajuste de tamanho diferenciado para BONK
            current_size = SIZE_USDC
            if symbol == 'kBONK_USDC_PERP':
                current_size = 50.0 # $50 para BONK
            
            qty = current_size / price
            
            # Ajustes específicos de Quantidade e Preço
            if symbol == 'WIF_USDC_PERP' or symbol == 'JUP_USDC_PERP':
                qty = int(qty)
            elif symbol == 'kBONK_USDC_PERP':
                step_size = 100
                qty = int(qty / step_size) * step_size
                qty = str(qty) # Passar como string
            else:
                qty = round(qty, 2)
            
            print(f"    {symbol}: Preço Atual ${last_price}. Tentando Limit Buy...")
            
            # Tentativa 1: Last Price
            # Se for kBONK, usar lógica especial
            if symbol == 'kBONK_USDC_PERP':
                price = last_price * 0.998 # 0.2% abaixo
                price = round(price, 6)
                payload = {
                    "symbol": symbol,
                    "side": "Bid",
                    "orderType": "Limit",
                    "quantity": str(qty),
                    "price": str(price),
                    "postOnly": True,
                    "selfTradePrevention": "RejectTaker"
                }
                import requests
                headers = auth.get_headers(instruction="orderExecute", params=payload)
                url = "https://api.backpack.exchange/api/v1/order"
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    order = response.json()
                    print(f"      Ordem BONK Criada! ID: {order.get('id')} @ ${price}")
                else:
                    print(f"      Falha BONK: {response.text}")
                continue # Pula lógica padrão
            
            # Lógica Padrão para os demais
            order = trade.execute_order(
                symbol=symbol,
                side="Bid",
                price=price,
                quantity=qty,
                order_type="Limit",
                post_only=True
            )
            
            if order:
                print(f"      Ordem Criada! ID: {order.get('id')} @ ${price}")
            else:
                print(f"     ️ Post Only rejeitou em ${price}. Tentando 0.1% abaixo...")
                # Tentativa 2: 0.1% abaixo
                price = price * 0.999
                # Ajustar precisão de preço (SOL 2 casas, WIF 4 casas, ETH 2 casas)
                if 'WIF' in symbol: price = round(price, 4)
                elif 'JUP' in symbol: price = round(price, 4)
                else: price = round(price, 2)
                
                order = trade.execute_order(
                    symbol=symbol,
                    side="Bid",
                    price=price,
                    quantity=qty,
                    order_type="Limit",
                    post_only=True
                )
                if order:
                     print(f"      Ordem Ajustada Criada! ID: {order.get('id')} @ ${price}")
                else:
                     print(f"      Falha final em {symbol}.")

        except Exception as e:
            print(f"    Erro em {symbol}: {e}")

    print("\n ACTIVE SNIPER CONCLUÍDO.")
    print("   Monitore o Recovery Dashboard.")

if __name__ == "__main__":
    run_active_sniper()
