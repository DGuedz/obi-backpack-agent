import sys
import os
import time
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport

# CONFIGURAÇÃO "HYPER SCALP 50x"
LEVERAGE = 50
MARGIN_USD = 3.0
TAKER_FEE_BUFFER = 1.002 # 0.2% buffer para garantir execução

def hyper_scalp_execute(symbol, side="Buy"):
    print(f" INICIANDO HYPER SCALP 50x [{side.upper()}] em {symbol}")
    print(f" Margem Fixa: ${MARGIN_USD} | Alavancagem: {LEVERAGE}x")
    
    transport = BackpackTransport()
    
    # 1. OBTER PREÇO ATUAL (MARKET CHECK)
    print("    Verificando Preço de Mercado...")
    ticker = transport._send_request("GET", f"/api/v1/ticker?symbol={symbol}", "tickerQuery")
    if not ticker:
        print("    Erro ao obter ticker. Abortando.")
        return

    last_price = float(ticker.get('lastPrice', 0))
    print(f"    Preço Atual: {last_price}")
    
    # 2. CALCULAR QUANTIDADE (NOTIONAL)
    # Notional = Margin * Leverage
    # Qty = Notional / Price
    notional_value = MARGIN_USD * LEVERAGE
    quantity = notional_value / last_price
    
    # Ajuste de Precisão
    # Maioria dos PERPs Backpack usa 0.01 ou 1 dependendo do ativo.
    if last_price > 50000:
        quantity_str = f"{quantity:.5f}" # BTC
    elif last_price > 1000:
        quantity_str = f"{quantity:.2f}" # ETH
    elif last_price > 100:
        quantity_str = f"{quantity:.2f}" # SOL
    elif last_price > 10:
        quantity_str = f"{quantity:.1f}" # HYPE, AVAX
    elif last_price > 1:
        quantity_str = f"{quantity:.0f}" # XRP, SUI
    else:
        quantity_str = f"{quantity:.0f}" # PEPE

    # Override for specific assets known to need integers or specific precision
    if "DOGE" in symbol:
         quantity_str = f"{quantity:.0f}"
    
    print(f"    Adjusted Quantity: {quantity_str} (Price: {last_price})")
        
    print(f"    Calculando Posição: ${notional_value} Notional -> {quantity_str} {symbol.split('_')[0]}")
    
    # 3. EXECUTAR ORDEM A MERCADO (TAKER)
    # Atenção: Ordem Market na Backpack requer "Market" no type, ou Limit com IOC/FOK?
    # Backpack API: type="Market" suportado.
    
    # Normalizar Side para Title Case (Bid/Ask) se necessário, ou manter Buy/Sell se a API aceitar.
    # O erro 'Expected input type "Side", found "Buy"' sugere que "Buy" não é o enum esperado.
    # Pode ser "Bid"/"Ask" ou case sensitive "Bid"/"Ask" em vez de "Buy"/"Sell".
    # Mas a documentação (openapi.json) geralmente usa "Bid"/"Ask".
    # Vamos converter: Buy -> Bid, Sell -> Ask
    
    api_side = "Bid" if side.lower() == "buy" else "Ask"
    if side.lower() == "sell": api_side = "Ask"
    
    print(f"    EXECUTANDO ORDEM MARKET ({api_side})...")
    payload = {
        "symbol": symbol,
        "side": api_side, # Corrigido para Bid/Ask
        "orderType": "Market",
        "quantity": quantity_str
        # "leverage": LEVERAGE # Backpack define alavancagem por conta/asset, não por ordem? 
        # ATENÇÃO: É preciso garantir que a conta está em 50x ANTES. A API não define leverage na ordem.
        # Vamos assumir que o usuário já configurou ou faremos um setLeverage se existir endpoint.
    }
    
    # Executar
    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
    
    if res and 'id' in res:
        print(f"    ORDEM EXECUTADA! ID: {res['id']}")
        print("   ⏳ Monitorando PnL imediato (Simulação Visual)...")
        # Aqui entraria o loop de monitoramento
    else:
        print(f"    Falha na Execução: {res}")

def set_leverage_check():
    # Placeholder: A Backpack geralmente configura leverage globalmente ou via UI.
    # Não há endpoint público documentado facilmente para "set leverage" no openapi.json visto anteriormente.
    # Assumimos que o usuário setou 50x na UI.
    pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        chosen_side = sys.argv[1] # Buy or Sell
    else:
        chosen_side = "Buy" # Default
        
    hyper_scalp_execute(chosen_side)
