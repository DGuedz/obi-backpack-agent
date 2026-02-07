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

def diagnose():
    print("️‍️ DIAGNOSTICANDO FUNDOS E MERCADO...", flush=True)
    transport = BackpackTransport()
    
    # 1. Check Spot Assets
    print("\n [1] CHECANDO SALDO SPOT (Assets)...", flush=True)
    try:
        spot_assets = transport.get_assets()
        print(f"   -> Resposta Raw: {json.dumps(spot_assets, indent=2)}")
    except Exception as e:
        print(f"    Erro ao ler Spot: {e}")

    # 2. Check Futures Balance
    print("\nFuturos [2] CHECANDO SALDO FUTUROS (Collateral)...")
    try:
        futures_balance = transport.get_capital()
        print(f"   -> Resposta Raw: {json.dumps(futures_balance, indent=2)}")
    except Exception as e:
        print(f"    Erro ao ler Futuros: {e}")

    # 3. Check BTC Price Action
    print("\n [3] ANALISANDO BTC-PERP...")
    try:
        klines = transport.get_klines("BTC_USDC", "15m", limit=5)
        if klines:
            last_close = klines[-1]['close']
            print(f"   -> Preço Atual: {last_close}")
            print(f"   -> Últimos 5 candles: {[k['close'] for k in klines]}")
        else:
            print("   ️ Nenhum dado de kline recebido.")
            
        ticker = transport.get_market_ticker("BTC_USDC")
        print(f"   -> Ticker: {json.dumps(ticker, indent=2)}")
            
    except Exception as e:
        print(f"    Erro ao ler Mercado: {e}")

if __name__ == "__main__":
    diagnose()
