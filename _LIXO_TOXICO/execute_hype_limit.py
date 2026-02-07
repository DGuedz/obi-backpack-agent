import os
import sys
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

# --- Configuração ---
SYMBOL = "HYPE_USDC_PERP"
LEVERAGE = 10
MARGIN_USD = 50  # Valor a investir da margem
SL_PERCENT = 0.02
TP_PERCENT = 0.05

def execute_entry():
    print(f" Iniciando Execução Sniper em {SYMBOL}...")
    
    api_key = os.getenv('BACKPACK_API_KEY')
    private_key = os.getenv('BACKPACK_API_SECRET')
    
    if not api_key:
        print(" API Key missing")
        return

    auth = BackpackAuth(api_key, private_key)
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # 1. Verificar Saldo
    print(" Verificando Saldo Disponível...")
    balances = data.get_balances()
    if not balances:
        print(" Erro ao obter saldo.")
        return

    usdc_balance = 0
    if 'USDC' in balances:
        usdc_balance = float(balances['USDC']['available'])
    
    print(f"   Saldo USDC Disponível: ${usdc_balance:.2f}")
    
    if usdc_balance < 5: # Mínimo de segurança
        print(" Saldo insuficiente para operar.")
        return

    # Ajustar margem se saldo for menor que o desejado
    trade_margin = min(MARGIN_USD, usdc_balance * 0.95) # Deixar 5% de buffer
    if trade_margin < 5:
        print(" Margem calculada muito baixa (< $5).")
        return
        
    print(f"   Margem para o Trade: ${trade_margin:.2f}")

    # 1.5 Obter Regras do Mercado (Tick Size e Step Size)
    print(" Obtendo Regras de Mercado...")
    markets = data.get_markets()
    market_info = next((m for m in markets if m['symbol'] == SYMBOL), None)
    
    if not market_info:
        print(f" Mercado {SYMBOL} não encontrado.")
        return
        
    # Filters
    price_filter = market_info.get('filters', {}).get('price', {})
    qty_filter = market_info.get('filters', {}).get('quantity', {})
    
    tick_size = float(price_filter.get('tickSize', '0.000001'))
    step_size = float(qty_filter.get('stepSize', '1'))
    
    print(f"   Tick Size: {tick_size} | Step Size: {step_size}")

    # Função auxiliar para arredondar
    def round_step(value, step):
        return round(value / step) * step

    # 2. Obter Preço de Mercado (Ticker e Book)
    print(f" Analisando Book de {SYMBOL}...")
    # ticker = data.get_ticker(SYMBOL)
    # last_price = float(ticker['lastPrice'])
    
    depth = data.get_orderbook_depth(SYMBOL, limit=5)
    if not depth or not depth.get('bids'):
        print(" Book vazio ou erro ao obter depth.")
        return

    best_bid = float(depth['bids'][0][0])
    best_ask = float(depth['asks'][0][0])
    
    print(f"   Best Bid: {best_bid} | Best Ask: {best_ask}")
    
    # Estratégia Maker: Colocar no Top Bid
    target_entry_price = best_bid
    
    # Ajustar Preço ao Tick Size
    target_entry_price = round_step(target_entry_price, tick_size)
    
    # Formatar preço para string com casas decimais corretas
    # Ex: se tick_size 0.000001, precisa de 6 casas.
    import decimal
    d = decimal.Decimal(str(tick_size))
    decimals = abs(d.as_tuple().exponent)
    price_str = f"{target_entry_price:.{decimals}f}"

    print(f"   Alvo Limit (Maker - Top Bid): {price_str}")
    
    # 3. Calcular Quantidade
    # Quantity = (Margin * Leverage) / Price
    quantity = (trade_margin * LEVERAGE) / target_entry_price
    
    # Ajustar Quantidade ao Step Size
    quantity = round_step(quantity, step_size)
    
    # Formatar quantidade
    # Se step_size for 1, 0 casas. Se 0.1, 1 casa.
    d_qty = decimal.Decimal(str(step_size))
    qty_decimals = abs(d_qty.as_tuple().exponent)
    qty_str = f"{quantity:.{qty_decimals}f}"
    
    print(f"   Quantidade Calculada (10x): {qty_str} HYPE")
    
    if float(qty_str) <= 0:
        print(" Quantidade inválida.")
        return

    # 4. Enviar Ordem Limit
    print(f" Enviando Ordem Limit de Compra...")
    print(f"   Side: Bid | Price: {price_str} | Qty: {qty_str}")
    
    res = trade.execute_order(
        symbol=SYMBOL,
        side="Bid",
        price=price_str,
        quantity=qty_str,
        order_type="Limit",
        post_only=True # Garantir Maker
    )
    
    if res and 'id' in res:
        print(f" Ordem Limit Enviada com Sucesso! ID: {res['id']}")
        
        # Calcular Preços de TP e SL para exibir
        sl_price = target_entry_price * (1 - SL_PERCENT)
        tp_price = target_entry_price * (1 + TP_PERCENT)
        
        print("\n️ PLANO DE VOO (Configurar Manulamente ou via Script de Monitoramento):")
        print(f"   Stop Loss (2%): {sl_price:.5f}")
        print(f"   Take Profit (5%): {tp_price:.5f}")
        print("️ A ordem de SL/TP só deve ser enviada após a execução da entrada.")
        
    else:
        print(" Falha ao enviar ordem. Pode ser que o preço moveu ou PostOnly rejeitou (Taker).")
        # Retry logic could go here (e.g., try best bid)

if __name__ == "__main__":
    execute_entry()
