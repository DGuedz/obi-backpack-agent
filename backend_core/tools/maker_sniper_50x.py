import sys
import os
import time
import requests
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport

# CONFIGURAÇÃO SNIPER GLOBAL
# (Sobrescrita se rodar como módulo)
LEVERAGE = 50
MARGIN_USD = 3.0
MAX_LOSS_USD = 0.10  # 10 centavos
TARGET_ROE = 0.05    # 5% sobre a margem

def get_best_book_price(transport, symbol, side):
    """Obtém o melhor preço do book para apregoar (Best Bid + Tick ou Best Ask - Tick)"""
    try:
        ticker = transport._send_request("GET", f"/api/v1/ticker?symbol={symbol}", "tickerQuery")
        if side == "Buy":
            return float(ticker['bestBid'])
        else:
            return float(ticker['bestAsk'])
    except:
        return None

def maker_sniper(symbol, side="Buy"):
    # Usar SYMBOL passado como argumento
    print(f" INICIANDO SNIPER MAKER 50x [{side}] em {symbol}")
    print(f" Margem: ${MARGIN_USD} | SL: ${MAX_LOSS_USD} | TP: {TARGET_ROE*100}% ROE")
    
    transport = BackpackTransport()
    
    # 1. CALCULAR TAMANHO
    ticker = transport._send_request("GET", f"/api/v1/ticker?symbol={symbol}", "tickerQuery")
    if not ticker:
        print(f"    Erro ao ler ticker de {symbol}. Abortando.")
        return
        
    current_price = float(ticker['lastPrice'])
    if current_price <= 0: return

    notional = MARGIN_USD * LEVERAGE
    qty = notional / current_price
    
    # Ajuste de Precisão
    # Maioria dos PERPs Backpack usa 0.01 ou 1 dependendo do ativo.
    # Vamos usar formatação dinâmica baseada no preço.
    if current_price > 1000:
        qty_str = f"{qty:.5f}" # BTC, ETH
    elif current_price > 10:
        qty_str = f"{qty:.2f}" # SOL, AVAX, HYPE
    else:
        # DOGE, LIT (< 2.0) -> Tentar 1 casa decimal
        # Inteiro pode ser demais (0), 1 casa é seguro?
        # Erro "Quantity decimal too long" sugere que eles querem MENOS casas.
        qty_str = f"{qty:.1f}"
        
    # Check Min Quantity? Assume Backpack accepts small decimals for most.
    
    print(f"    Size: {qty_str} {symbol} (~${notional:.2f})")
    
    # 2. COLOCAR ORDEM MAKER (LIMIT POST ONLY)
    order_id = None
    filled = False
    entry_price = 0.0
    
    attempts = 0
    # Aumentando tentativas e reduzindo sleep para ser mais "Sniper"
    while not filled and attempts < 10:
        attempts += 1
        print(f"    Tentativa de Apregoar #{attempts}...")
        
        # Get Price
        price = get_best_book_price(transport, symbol, side)
        if not price: continue
        
        limit_price = price 
        
        # Formatar Preço (Backpack é chato com tick size)
        # Vamos confiar que o 'bestBid' já vem formatado corretamente.
        
        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": "Limit",
            "quantity": qty_str,
            "price": str(limit_price),
            "postOnly": True # GARANTIA DE MAKER
        }
        
        res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        
        if res and 'id' in res:
            order_id = res['id']
            # print(f"       Ordem Enviada: {order_id}. Aguardando Fill...")
            
            # Esperar 2s (Rápido)
            for _ in range(4):
                time.sleep(0.5)
                # Check status
                status = transport._send_request("GET", f"/api/v1/order?symbol={SYMBOL}&orderId={order_id}", "orderQuery")
                if status and status.get('status') == 'Filled':
                    filled = True
                    entry_price = float(status.get('avgFillPrice', limit_price))
                    print(f"       EXECUTADO! Preço Médio: {entry_price}")
                    break
                elif status and status.get('status') in ['Canceled', 'Expired']:
                    # print("       Cancelada/Expirada (PostOnly rejeitou?).")
                    break
            
            if not filled:
                # Cancelar para reposicionar
                transport._send_request("DELETE", "/api/v1/orders", "orderCancelAll", {"symbol": SYMBOL})
        else:
            # print(f"       Erro ao enviar ordem: {res}")
            time.sleep(0.5)

    if not filled:
        print("    Falha ao entrar como Maker após 10 tentativas. Abortando.")
        return

    # 3. GERENCIAMENTO DA POSIÇÃO (BRACKET)
    print("\n️ ATIVANDO ESCUDO BRACKET (SL/TP)...")
    
    delta_price_tp = (MARGIN_USD * TARGET_ROE) / qty
    delta_price_sl = MAX_LOSS_USD / qty
    
    if side == "Buy":
        tp_price = entry_price + delta_price_tp
        sl_price = entry_price - delta_price_sl
    else:
        tp_price = entry_price - delta_price_tp
        sl_price = entry_price + delta_price_sl
        
    print(f"    TP Alvo: {tp_price:.4f}")
    print(f"    SL Alvo: {sl_price:.4f}")
    
    exit_side = "Sell" if side == "Buy" else "Buy"
    
    # TP ORDER (Limit Maker Exit)
    tp_payload = {
        "symbol": SYMBOL,
        "side": exit_side,
        "orderType": "Limit",
        "quantity": qty_str,
        "price": f"{tp_price:.4f}", # Try 4 decimals generally
        "postOnly": True 
    }
    tp_res = transport._send_request("POST", "/api/v1/order", "orderExecute", tp_payload)
    
    # LOOP DE MONITORAMENTO (SL)
    # print("    MONITORANDO PREÇO...")
    position_open = True
    start_time = time.time()
    
    while position_open:
        time.sleep(0.5)
        
        # Timeout de segurança? (Ex: 10 min)
        if time.time() - start_time > 600:
            print("   ⏰ Timeout (10min). Fechando posição...")
            stop_hit = True # Force close
        
        ticker = transport._send_request("GET", f"/api/v1/ticker?symbol={SYMBOL}", "tickerQuery")
        curr_price = float(ticker['lastPrice'])
        
        # Checar SL
        stop_hit = False
        if side == "Buy" and curr_price <= sl_price: stop_hit = True
        if side == "Sell" and curr_price >= sl_price: stop_hit = True
        
        if stop_hit:
            print(f"    STOP LOSS ATINGIDO! Preço: {curr_price}. Fechando a Mercado...")
            transport._send_request("DELETE", "/api/v1/orders", "orderCancelAll", {"symbol": SYMBOL})
            close_payload = {
                "symbol": SYMBOL,
                "side": exit_side,
                "orderType": "Market",
                "quantity": qty_str
            }
            transport._send_request("POST", "/api/v1/order", "orderExecute", close_payload)
            print("    Posição Fechada no SL.")
            position_open = False
            
        # Checar TP
        if tp_res and 'id' in tp_res:
            tp_status = transport._send_request("GET", f"/api/v1/order?symbol={SYMBOL}&orderId={tp_res['id']}", "orderQuery")
            if tp_status and tp_status.get('status') == 'Filled':
                print(f"    TAKE PROFIT EXECUTADO! Preço: {tp_status.get('avgFillPrice')}")
                position_open = False

if __name__ == "__main__":
    side_arg = sys.argv[1] if len(sys.argv) > 1 else "Buy"
    maker_sniper(side_arg)
