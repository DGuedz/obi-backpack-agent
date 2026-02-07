import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from fire_scanner import FireScanner

load_dotenv()

def monitor_goal():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    GOAL = 300.0
    
    print(" MONITOR DE META: RUMO AOS $300 (COCKPIT)")
    print("==========================================")
    
    # 1. Saldo e Equity
    balances = data.get_balances()
    usdc_avail = float(balances.get('USDC', {}).get('available', 0))
    usdc_locked = float(balances.get('USDC', {}).get('locked', 0))
    total_wallet = usdc_avail + usdc_locked
    
    # Obter Equity (considerando PnL não realizado)
    unrealized_pnl = 0
    positions = data.get_positions()
    
    print(f"\n1. Posições Ativas:")
    has_pos = False
    active_symbols = []
    
    for p in positions:
        qty = float(p.get('netQuantity', 0))
        if qty != 0:
            has_pos = True
            symbol = p['symbol']
            active_symbols.append(symbol)
            entry = float(p['entryPrice'])
            
            # Preço atual
            ticker = data.get_ticker(symbol)
            curr_price = float(ticker['lastPrice'])
            
            pnl = (curr_price - entry) * qty
            
            unrealized_pnl += pnl
            roi = (pnl / (abs(qty) * entry / 3)) * 100 # Est. 3x
            
            print(f"   🟢 {symbol}: {qty} @ ${entry:.2f} -> ${curr_price:.2f}")
            print(f"      PnL: ${pnl:.2f} ({roi:.2f}%)")

    if not has_pos:
        print("   (Nenhuma posição ativa no momento)")

    total_equity = total_wallet + unrealized_pnl
    distance = GOAL - total_equity
    progress = (total_equity / GOAL) * 100
    
    print(f"\n2. Status Financeiro:")
    print(f"    Wallet Balance: ${total_wallet:.2f}")
    print(f"    Unrealized PnL: ${unrealized_pnl:.2f}")
    print(f"    TOTAL EQUITY:   ${total_equity:.2f}")
    print(f"    META:           ${GOAL:.2f}")
    print(f"    Falta:          ${distance:.2f}")
    
    bar_len = 20
    filled = int(progress / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\n   Progresso: [{bar}] {progress:.1f}%")

if __name__ == "__main__":
    while True:
        try:
            monitor_goal()
        except Exception as e:
            print(f"Erro: {e}")
        time.sleep(10)
