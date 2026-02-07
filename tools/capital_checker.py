import os
import sys
import json
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def check_capital():
    load_dotenv()
    transport = BackpackTransport()
    
    print("\n CAPITAL CHECKER")
    print("=" * 60)
    
    # 1. Posições Abertas (Unrealized PnL)
    print("⏳ Buscando Posições...")
    positions = transport.get_positions()
    unrealized_pnl = 0.0
    
    if positions:
        print("\n POSIÇÕES ABERTAS:")
        print(f"{'SYMBOL':<15} | {'SIDE':<5} | {'ENTRY':<10} | {'MARK':<10} | {'UPNL':<10}")
        print("-" * 60)
        for p in positions:
            sym = p['symbol']
            qty = float(p['netQuantity'])
            entry = float(p['entryPrice'])
            mark = float(p['markPrice'])
            
            side = "LONG" if qty > 0 else "SHORT"
            upnl = (mark - entry) * qty
            unrealized_pnl += upnl
            
            print(f"{sym:<15} | {side:<5} | {entry:<10.4f} | {mark:<10.4f} | ${upnl:+.2f}")
    else:
        print("\n Nenhuma posição aberta.")
        
    # 2. Saldo/Equity
    print("\n⏳ Buscando Equity...")
    collateral = transport.get_account_collateral()
    
    equity = 0.0
    balance = 0.0
    
    if collateral:
        # Tentar extrair equity
        # Na V1, geralmente é 'totalEquity' ou soma dos balances + upnl
        # Se for Unified, deve ter um campo total.
        
        # Estrutura comum: {'USDC': {'available': ..., 'equity': ...}}
        # Vamos somar o equity de USDC (moeda base)
        
        if 'netEquity' in collateral:
             equity = float(collateral['netEquity'])
        elif 'USDC' in collateral:
            equity = float(collateral['USDC'].get('equity', 0))
            balance = float(collateral['USDC'].get('available', 0)) # ou walletBalance
        elif 'total' in collateral:
             equity = float(collateral['total'].get('equity', 0))
        else:
            # Fallback: tentar encontrar USDC na lista se for lista
            pass
        
        # If equity is still 0, print raw to debug
        if equity == 0:
             print("\n️ EQUITY 0 DETECTADO. DUMP RAW:")
             print(json.dumps(collateral, indent=2))
        
        print("-" * 60)
        print(f" WALLET BALANCE: ${balance:.2f} (Aprox)")
        print(f" TOTAL EQUITY:   ${equity:.2f}")
        print(f" UNREALIZED PnL: ${unrealized_pnl:+.2f}")
        print("=" * 60)
        
        # Comparação com Capital Inicial ($600)
        start_cap = 600.0
        pnl_total = equity - start_cap
        roi = (pnl_total / start_cap) * 100
        
        print(f" PERFORMANCE TOTAL: ${pnl_total:+.2f} ({roi:+.2f}%)")
        
        if pnl_total > 0:
            print(" LUCRO CONFIRMADO! O SISTEMA FUNCIONA.")
        else:
            print(" DRAWDOWN ATUAL. AVALIAR RETRAÇÃO.")
            
    else:
        print(" Erro ao buscar collateral.")
        print(json.dumps(collateral, indent=2))

if __name__ == "__main__":
    check_capital()
