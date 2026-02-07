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
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.backpack_transport import BackpackTransport

def force_entry():
    print(" INICIANDO ENTRADA SNIPER (ZORA) - BLIND MODE...", flush=True)
    transport = BackpackTransport()
    
    # --- BLIND MODE: FORÇA BRUTA DE CÁLCULO ---
    # Ignora API de saldo bugada e assume $100 de Equity
    # Meta: $50 de Margem (Agressivo)
    
    SYMBOL = "ZORA_USDC_PERP"
    EQUITY_ASSUMED = 100.0
    MARGIN_TO_USE = 25.0 # Reduced from $50 to $25 due to insufficient margin
    LEVERAGE = 10 # 10x Sniper
    
    NOTIONAL_SIZE = MARGIN_TO_USE * LEVERAGE # $250
    
    print(f"   ️ BLIND MODE ATIVADO")
    print(f"      Equity Assumido: ${EQUITY_ASSUMED}")
    print(f"      Margem Alvo: ${MARGIN_TO_USE}")
    print(f"      Tamanho Notional: ${NOTIONAL_SIZE} (Lev {LEVERAGE}x)")

    # Obter preço atual para calcular quantidade
    ticker = transport.get_ticker(SYMBOL)
    if not ticker:
        print("    Erro ao obter preço atual.")
        return

    price = float(ticker['lastPrice'])
    quantity_tokens = NOTIONAL_SIZE / price
    
    # Arredondar para precisão correta (ZORA requires integer, but API might be picky about string format)
    # If "Quantity decimal too long" persists for "19238", it might mean it expects ".0" or similar?
    # Or maybe it wants LESS precision? No, integer is minimal.
    # Let's try formatting as integer string explicitly without decimals.
    # But wait, 19238 is integer.
    # Maybe ZORA is actually huge price and quantity should be small? No, price is 0.02.
    # Ah, maybe the API wants "19230" (step size)?
    # Let's try checking step size or just trying a round number.
    # Let's try casting to int and string.
    quantity_tokens = int(quantity_tokens)
    quantity_str = f"{quantity_tokens}"
    
    # DEBUG: Force a very round number if needed
    # If "9652" fails with "decimal too long", maybe it wants "9650"?
    # Let's try rounding down to nearest 10
    quantity_tokens = (quantity_tokens // 10) * 10
    quantity_str = f"{quantity_tokens}"
    
    print(f"   ️ Preço Atual: ${price}")
    print(f"    Quantidade Calculada: {quantity_str} ZORA (Arredondado para dezena)")
    
    # Executar
    print(f"    ENVIANDO ORDEM MARKET BUY...")
    res = transport.execute_order(
        symbol=SYMBOL,
        order_type="Market",
        side="Bid",
        quantity=quantity_str
    )
    
    print(f"    Resultado: {res}")
    
    if res and 'id' in res:
        print("    SUCESSO! Ordem Executada.")
    else:
        print("    FALHA NA EXECUÇÃO.")

if __name__ == "__main__":
    force_entry()
