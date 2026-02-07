import os
import time
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path para importar módulos core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport

def run_night_duo():
    print(" NIGHT DUO SNIPER: Initializing 2-Trade Strategy (5x Leverage)...")
    
    trade = BackpackTransport()
    
    # Alvos Selecionados pelo Scanner (Bear Waves)
    targets = [
        {"symbol": "ETH_USDC_PERP", "side": "Ask", "leverage": 5, "amount_usd": 100}, # Short ETH (OBI -0.99)
        {"symbol": "SUI_USDC_PERP", "side": "Ask", "leverage": 5, "amount_usd": 100}  # Short SUI (OBI -0.70)
    ]
    
    # Parâmetros de Proteção (Swing Trade Curto)
    # 5x Leverage -> 1% move = 5% PnL.
    # Alvo Lucro: 5% movimento (25% ROE).
    # Stop Loss: 2% movimento (10% ROE) - Apertado para evitar drawdowns grandes.
    TP_PCT = 0.05 
    SL_PCT = 0.02

    print(f" Targets: {[t['symbol'] for t in targets]}")
    print(f"️  Leverage: 5x | Notional: $100 USD each | TP: {TP_PCT*100}% | SL: {SL_PCT*100}%")
    
    for target in targets:
        symbol = target['symbol']
        side = target['side']
        lev = target['leverage']
        usd_amount = target['amount_usd']
        
        print(f"\n Executing {side} on {symbol}...")
        
        # 1. Obter Preço Atual
        ticker = trade.get_ticker(symbol)
        if not ticker:
            print(f"    Failed to get ticker for {symbol}. Skipping.")
            continue
            
        price = float(ticker['lastPrice'])
        quantity = usd_amount / price
        
        # Ajustar precisão da quantidade (simplificado)
        if price > 100:
            quantity = round(quantity, 3)
        else:
            quantity = round(quantity, 1)
            
        print(f"    Price: {price} | Qty: {quantity} ({usd_amount} USD)")
        
        # 2. Executar Ordem a Mercado
        # Side 'Ask' = Venda (Short)
        # Side 'Bid' = Compra (Long)
        order = trade.execute_order(
            symbol=symbol,
            side=side,
            order_type="Market",
            quantity=str(quantity),
            price=None # Market order
        )
        
        if order:
            print(f"    Order Executed! ID: {order.get('id', 'Unknown')}")
            
            # 3. Configurar SL/TP (Ordem Condicional)
            # Para Short (Ask): TP é Compra (Bid) abaixo do preço. SL é Compra (Bid) acima do preço.
            # Para Long (Bid): TP é Venda (Ask) acima do preço. SL é Venda (Ask) abaixo do preço.
            
            if side == "Ask": # SHORT
                tp_price = price * (1 - TP_PCT)
                sl_price = price * (1 + SL_PCT)
                exit_side = "Bid"
            else: # LONG
                tp_price = price * (1 + TP_PCT)
                sl_price = price * (1 - SL_PCT)
                exit_side = "Ask"
                
            # Formatar preços
            if price > 1000:
                tp_price = round(tp_price, 1)
                sl_price = round(sl_price, 1)
            elif price > 10:
                tp_price = round(tp_price, 2)
                sl_price = round(sl_price, 2)
            else:
                tp_price = round(tp_price, 4)
                sl_price = round(sl_price, 4)

            print(f"   ️  Setting Protection: SL @ {sl_price} | TP @ {tp_price}")
            
            # Stop Loss (Trigger Market)
            sl_order = trade.execute_order(
                symbol=symbol,
                side=exit_side,
                order_type="TriggerMarket",
                quantity=str(quantity),
                price=None,
                trigger_price=str(sl_price)
            )
            if sl_order:
                 print(f"       SL Set: {sl_order.get('id')}")
            else:
                 print(f"       Failed to set SL")

            # Take Profit (Limit) - Backpack suporta TP como Limit ou Trigger?
            # Vamos usar Limit simples para TP se for ordem Maker, mas para garantir saída, TriggerLimit ou Limit.
            # Se for Short, TP é Buy Limit abaixo do preço.
            tp_order = trade.execute_order(
                symbol=symbol,
                side=exit_side,
                order_type="Limit",
                quantity=str(quantity),
                price=str(tp_price)
            )
            if tp_order:
                 print(f"       TP Set: {tp_order.get('id')}")
            else:
                 print(f"       Failed to set TP")
                 
        else:
            print(f"    Execution Failed. Check balance or API logs.")

if __name__ == "__main__":
    run_night_duo()
