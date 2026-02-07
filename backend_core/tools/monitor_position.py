import os
import sys
import time
from tabulate import tabulate

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'obiwork_core'))

from obiwork_core.core.backpack_transport import BackpackTransport
from obiwork_core.core.backpack_data import BackpackData
from obiwork_core.core.backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

def main():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print("\n️ MONITOR DE POSIÇÕES (50x WATCH)")
    print("-" * 60)
    
    # 1. Obter Tickers (Preço Atual)
    tickers = data.get_tickers()
    prices = {t['symbol']: float(t['lastPrice']) for t in tickers}
    
    # 2. Obter Posições
    # Endpoint de Posições não estava no BackpackData original, vamos usar o Transport ou requests direto
    # BackpackData.get_account_collateral dá margem, mas não posições detalhadas (depende da impl)
    # Vamos usar endpoint direto de posições: GET /api/v1/positions
    
    endpoint = "/api/v1/position" # Singular!
    url = f"{data.base_url}{endpoint}"
    import requests
    
    # Assinatura manual pois get_positions não está na classe
    instruction = "positionQuery"
    headers = auth.get_headers(instruction=instruction)
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"Erro API: {res.text}")
            return
        positions = res.json()
    except Exception as e:
        print(f"Erro Req: {e}")
        return

    table_data = []
    has_btc = False
    
    for p in positions:
        symbol = p['symbol']
        qty = float(p['netQuantity'])
        if qty == 0: continue
        
        entry = float(p['entryPrice'])
        curr = prices.get(symbol, entry)
        leverage = p.get('leverage', 'N/A')
        
        # PnL Calc
        if qty > 0:
            pnl_pct = (curr - entry) / entry
        else:
            pnl_pct = (entry - curr) / entry
            
        roe = pnl_pct * float(leverage) if leverage != 'N/A' else 0
        
        # Status
        status = "🟢 SAFE"
        if roe < -20: status = "️ DANGER"
        if roe < -50: status = " CRITICAL"
        if roe > 10: status = " PROFIT"
        
        if "BTC" in symbol: has_btc = True
        
        table_data.append([
            symbol,
            f"{leverage}x",
            f"{qty:.4f}",
            f"${entry:.2f}",
            f"${curr:.2f}",
            f"{roe*100:.2f}%",
            status
        ])
        
    print(tabulate(table_data, headers=["Symbol", "Lev", "Size", "Entry", "Current", "ROE %", "Status"], tablefmt="grid"))
    print("-" * 60)
    
    if has_btc:
        print(" Operação em BTC DETECTADA. Monitorando...")
    else:
        print(" Nenhuma posição em BTC encontrada.")

if __name__ == "__main__":
    main()
