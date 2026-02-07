import os
import sys
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

def check_positions():
    load_dotenv()
    
    transport = BackpackTransport()
    # auth is handled inside transport
    
    print("\n POSIÇÕES ABERTAS & MARGEM UTILIZADA")
    print("-" * 80)
    print(f"{'SYMBOL':<15} | {'SIDE':<5} | {'LEV':<3} | {'NOTIONAL($)':<12} | {'MARGIN($)':<10} | {'PNL($)':<10}")
    print("-" * 80)
    
    try:
        collateral = transport.get_account_collateral()
        print(f" BALANCE: ${collateral.get('availableToTrade', 'N/A')} (Equity: ${collateral.get('equity', 'N/A')})")
        
        positions = transport.get_positions()
        
        if not positions:
            print("Nenhuma posição encontrada ou erro na API.")
            return

        total_margin = 0
        total_notional = 0
        
        for p in positions:
            symbol = p.get('symbol')
            side = p.get('side')
            quantity = float(p.get('netQuantity'))
            if quantity == 0: continue
            
            # Identify side based on quantity sign if not explicit
            if side is None:
                side = "Long" if quantity > 0 else "Short"
            
            quantity = abs(quantity)
            entry_price = float(p.get('entryPrice'))
            mark_price = float(p.get('markPrice'))
            leverage = int(p.get('leverage', 1))
            pnl = float(p.get('unrealizedPnl', 0))
            
            notional = quantity * mark_price
            margin_used = notional / leverage
            
            total_margin += margin_used
            total_notional += notional
            
            print(f"{symbol:<15} | {side:<5} | {leverage:<3}x | ${notional:<11.2f} | ${margin_used:<9.2f} | ${pnl:<9.2f}")
            
        print("-" * 80)
        print(f"TOTAL MARGIN USED: ${total_margin:.2f}")
        print(f"TOTAL NOTIONAL:    ${total_notional:.2f}")
        print("-" * 80)
        
    except Exception as e:
        print(f"Erro ao buscar posições: {e}")

if __name__ == "__main__":
    check_positions()
