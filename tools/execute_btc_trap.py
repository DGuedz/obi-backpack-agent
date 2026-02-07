import os
import sys
import time
import json

# Fix imports robustly
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

try:
    from core.backpack_transport import BackpackTransport
except ImportError:
    # Fallback if running from tools/ directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.backpack_transport import BackpackTransport

def execute_trap_strategy():
    print(" INICIANDO EXECUÇÃO 'BTC TRAP STRATEGY'...", flush=True)
    transport = BackpackTransport()
    
    # 1. Obter Preço Atual
    print("    Analisando Mercado BTC-PERP...")
    ticker = transport.get_ticker("BTC_USDC") # Note: using public ticker if available or klines
    # Fallback to klines if get_ticker fails or not implemented
    price = 0
    try:
        klines = transport.get_klines("BTC_USDC", "1m", limit=1)
        if klines:
            price = float(klines[-1]['close'])
            print(f"   -> Preço Atual: ${price}")
        else:
            print("    Erro: Não foi possível obter preço.")
            return
    except Exception as e:
        print(f"    Erro na análise de mercado: {e}")
        return

    # 2. Configurar Trade
    # Capital: $50 Margin * 10x Leverage = $500 Notional
    notional_value = 500
    quantity = notional_value / price
    
    # Arredondar para precisão correta (3 casas decimais para BTC geralmente, ou verificar info)
    # BTC min size is usually 0.0001. 
    quantity = round(quantity, 3)
    
    print(f"    Setup: Long $500 (10x) | Qty: {quantity} BTC")
    
    # 3. Executar Ordem a Mercado
    print("    Executando Market Buy...")
    try:
        # side="Bid" for Buy
        result = transport.execute_order(
            symbol="BTC_USDC",
            order_type="Market",
            side="Bid",
            quantity=quantity
        )
        
        print(f"   -> Resultado API: {result}")
        
        if result and 'id' in result:
            print("    ORDEM EXECUTADA COM SUCESSO!")
            order_id = result['id']
            
            # 4. Configurar SL e TP (Opcional - via Limit/Stop orders subsequentes)
            # TP: +1.5%
            # SL: -1.0%
            tp_price = round(price * 1.015, 1)
            sl_price = round(price * 0.990, 1)
            
            print(f"   ️ Configurando Proteções: TP @ {tp_price} | SL @ {sl_price}")
            
            # TP Order (Limit Sell)
            transport.execute_order("BTC_USDC", "Limit", "Ask", quantity, price=tp_price)
            
            # SL Order (Stop Market Sell) - Backpack supports StopLimit or StopMarket?
            # Usually Trigger Order.
            transport.execute_order("BTC_USDC", "StopMarket", "Ask", quantity, trigger_price=sl_price)
            
        else:
            print("   ️ Ordem não confirmada (verifique saldo/erro).")
            
    except Exception as e:
        print(f"    ERRO NA EXECUÇÃO: {e}")

if __name__ == "__main__":
    execute_trap_strategy()
