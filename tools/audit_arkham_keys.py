import os
import sys
import json
import time

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

def audit_keys():
    print("️  AUDITORIA PROFUNDA DE CHAVES (OBI03 - MAIN WALLET)", flush=True)
    print("=================================================", flush=True)
    
    # Load from environment variables (Current Configuration)
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    API_KEY = os.getenv('BACKPACK_API_KEY')
    API_SECRET = os.getenv('BACKPACK_API_SECRET')
    
    if not API_KEY or not API_SECRET:
        print(" ERRO: Chaves não encontradas no .env")
        return
    
    print(f" Chave em Análise (do .env): {API_KEY[:10]}...", flush=True)
    
    # Instanciar Transport com chaves manuais
    transport = BackpackTransport(api_key=API_KEY, api_secret=API_SECRET)
    
    # 1. Teste de Conexão (Account Capital - Futures)
    print("\n[1] FUTURES: Verificando Saldo e Colateral...", flush=True)
    try:
        collateral = transport.get_capital()
        print(f"   RAW Response: {json.dumps(collateral, indent=2)}")
        
        if collateral and isinstance(collateral, dict):
            if 'code' in collateral and collateral['code'] == 'INVALID_CLIENT_REQUEST':
                print("    FALHA: Erro de Assinatura ou Chave Inválida.")
            else:
                equity = collateral.get('totalEquity', '0')
                avail = collateral.get('availableToTrade', '0')
                print(f"    CONEXÃO BEM SUCEDIDA!")
                print(f"    Equity Total: {equity}")
                print(f"    Disponível: {avail}")
        else:
            print("   ️ Resposta vazia ou inesperada.")
    except Exception as e:
        print(f"    EXCEÇÃO FUTURES: {e}")

    # 2. Teste de Spot (Assets)
    print("\n[2] SPOT: Verificando Carteira de Ativos...", flush=True)
    try:
        assets = transport.get_assets()
        # print(f"   RAW Response: {json.dumps(assets, indent=2)}") # Pode ser grande
        
        if assets and isinstance(assets, dict):
             if 'USDC' in assets:
                 print(f"    USDC Spot: {assets['USDC']['available']}")
                 print(f"    USDC Bloqueado: {assets['USDC']['locked']}")
             else:
                 print("   ️ USDC não encontrado na carteira Spot (Saldo 0 ou inexistente).")
             
             # Listar quaisquer ativos com saldo > 0
             print("    Ativos com saldo positivo:")
             found = False
             for symbol, data in assets.items():
                 # Check 'available', 'locked', 'staked'
                 total_asset = 0.0
                 try:
                    total_asset += float(data.get('available', 0))
                    total_asset += float(data.get('locked', 0))
                    total_asset += float(data.get('staked', 0))
                 except:
                    pass
                 
                 if total_asset > 0:
                     print(f"      - {symbol}: {data} (Total: {total_asset})")
                     found = True
             if not found:
                 print("      (Nenhum ativo encontrado)")
                 
    except Exception as e:
        print(f"    EXCEÇÃO SPOT: {e}")

    # 3. Histórico de Fills (Atividade Recente)
    print("\n[3] HISTÓRICO: Verificando Últimas Execuções (Fills)...", flush=True)
    try:
        history = transport.get_fill_history(limit=5)
        print(f"   RAW Response: {json.dumps(history, indent=2)}")
        
        if isinstance(history, list) and len(history) > 0:
            print(f"    Últimos {len(history)} trades encontrados:")
            for fill in history:
                print(f"      - {fill.get('timestamp')}: {fill.get('side')} {fill.get('symbol')} @ {fill.get('price')} (Qtd: {fill.get('quantity')})")
        elif isinstance(history, list) and len(history) == 0:
            print("    HISTÓRICO VAZIO. Esta conta parece nunca ter operado ou o histórico expirou.")
        else:
            print("   ️ Erro ao buscar histórico.")
            
    except Exception as e:
        print(f"    EXCEÇÃO HISTÓRICO: {e}")

    # 4. Ordens Abertas
    print("\n[4] ORDENS: Verificando Ordens Abertas...", flush=True)
    try:
        orders = transport.get_open_orders()
        # print(f"   RAW Response: {json.dumps(orders, indent=2)}")
        
        if isinstance(orders, list) and len(orders) > 0:
            print(f"    {len(orders)} Ordens Abertas encontradas:")
            for order in orders:
                print(f"      - {order.get('side')} {order.get('symbol')} Type: {order.get('orderType')} Price: {order.get('price')}")
        else:
            print("    Nenhuma ordem aberta encontrada.")
            
    except Exception as e:
        print(f"    EXCEÇÃO ORDENS: {e}")

if __name__ == "__main__":
    audit_keys()
