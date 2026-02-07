import os
import sys
import json
import time

# Add core path
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

from core.backpack_transport import BackpackTransport

def test_limit_order():
    print(" PROVA DE FOGO: Tentativa de Ordem Limit (USDC 0.00)...")
    
    transport = BackpackTransport()
    
    # Par: SOL_USDC_PERP (Min size is usually 0.01 or similar)
    # Vamos tentar comprar 0.1 SOL a $1.00 (Total $0.10 de custo)
    # Se falhar por 'Insufficient Funds', prova que a API vê saldo 0.
    
    symbol = "SOL_USDC_PERP"
    # Preço mais realista para não ser rejeitado por "Too far"
    # SOL está ~240? Vamos tentar $200
    price = "200.00" 
    quantity = "0.1"
    
    print(f"   -> Tentando Limit Buy {quantity} {symbol} @ ${price}...")
    
    try:
        # Enviar Ordem Limit
        result = transport.execute_order(
            symbol=symbol,
            order_type="Limit",
            side="Bid",
            quantity=quantity,
            price=price,
            time_in_force="GTC"
        )
        
        print(f"    Resposta da API: {result}")
        
        if result and 'id' in result:
            print("    ORDEM ACEITA! (O saldo existe mas a API de leitura estava mentindo/bugada)")
            # Cancelar imediatamente
            print("   ️ Cancelando ordem de teste...")
            transport.cancel_order(symbol, result['id'])
        else:
            print("    ORDEM REJEITADA (Provável saldo insuficiente)")
            
    except Exception as e:
        print(f"    Exceção: {e}")

if __name__ == "__main__":
    test_limit_order()
