import os
import sys
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade

def check_status():
    load_dotenv()
    
    # Check for API Keys
    if not os.getenv('BACKPACK_API_KEY') or not os.getenv('BACKPACK_API_SECRET'):
        print("\n ERRO: Chaves de API não encontradas no .env")
        print("   Configure BACKPACK_API_KEY e BACKPACK_API_SECRET.")
        return

    print("\n CHECK STATUS REPORT (LIVE CONNECTION)")
    print("="*50)

    try:
        # Initialize Core Modules
        # Using BackpackTransport which seems to have sync methods implemented in previous turns
        transport = BackpackTransport()
        
        # Initialize Trade (from LEGACY for execution if needed, or check structure)
        # auth = BackpackAuth(...)
        # trade = BackpackTrade(auth) # This class seems to be for execution mostly
        
        # 1. Saldo (Collateral)
        print("\n SALDO & MARGEM:")
        try:
            collateral = transport.get_account_collateral()
            if collateral:
                print(f"   -> Dados Recebidos: {collateral}")
                # Try to extract USDC available
                # Typical response: {'availableToTrade': '...', 'totalEquity': '...', ...}
                if isinstance(collateral, dict):
                     avail = collateral.get('availableToTrade', 'N/A')
                     equity = collateral.get('totalEquity', 'N/A')
                     print(f"   -> Disponível para Trade: ${avail}")
                     print(f"   -> Equity Total: ${equity}")
            else:
                print("   (Saldo Vazio ou Erro de Leitura)")
        except Exception as e:
            print(f"    Erro ao ler saldo: {e}")

        # 2. Posições
        print("\n POSIÇÕES ABERTAS:")
        try:
            positions = transport.get_positions()
            if positions:
                for p in positions:
                    symbol = p.get('symbol')
                    qty = p.get('netQuantity', p.get('quantity'))
                    entry = p.get('entryPrice')
                    side = p.get('side')
                    pnl = p.get('unrealizedPnl')
                    print(f"   -> {symbol}: {side} {qty} @ {entry} | PnL: {pnl}")
            else:
                print("   (Nenhuma posição ativa)")
        except Exception as e:
             print(f"    Erro ao ler posições: {e}")
        
        # 3. Ordens Abertas
        print("\n ORDENS ABERTAS:")
        try:
            orders = transport.get_open_orders()
            if orders:
                for o in orders:
                    oid = o.get('id')
                    symbol = o.get('symbol')
                    side = o.get('side')
                    otype = o.get('orderType')
                    price = o.get('price', o.get('triggerPrice', 'N/A'))
                    qty = o.get('quantity')
                    print(f"   -> {oid} | {symbol} {side} {otype} | Qty: {qty} | Price: {price}")
            else:
                print("   (Nenhuma ordem aberta)")
        except Exception as e:
             print(f"    Erro ao ler ordens: {e}")

        print("="*50 + "\n")
        print(" CONEXÃO ESTABELECIDA COM SUCESSO")

    except Exception as e:
        print(f"\n FALHA CRÍTICA DE CONEXÃO: {e}")
        print("   Verifique suas chaves de API e conexão de internet.")

if __name__ == "__main__":
    check_status()
