import asyncio
import os
import sys
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def check_status():
    print(" VERIFICANDO STATUS DA CONTA (AO VIVO)...")
    load_dotenv()
    transport = BackpackTransport()
    
    # 1. Checar Saldo e Colateral
    try:
        collateral = transport.get_account_collateral()
        print("\n SALDO & MARGEM:")
        print(f"   Equity Total:      ${float(collateral.get('netEquity', 0)):.2f}")
        print(f"   Available Trade:   ${float(collateral.get('netEquityAvailable', 0)):.2f}")
        print(f"   Margin Used:       ${float(collateral.get('initialMargin', 0)):.2f}")
        print(f"   Leverage Limit:    {collateral.get('maxLeverage', '?')}x")
    except Exception as e:
        print(f" Erro ao ler saldo: {e}")

    # 2. Checar Posições Abertas
    try:
        positions = transport.get_positions()
        print(f"\n POSIÇÕES ABERTAS ({len(positions)}):")
        if not positions:
            print("   (Nenhuma posição ativa)")
        
        for p in positions:
            symbol = str(p.get('symbol', 'Unknown'))
            side = str(p.get('side', 'Unknown'))
            qty = str(p.get('quantity', '0'))
            entry = str(p.get('entryPrice', '0'))
            pnl = str(p.get('unrealizedPnl', '0'))
            print(f"    {symbol} | {side} | Qty: {qty} | Entry: {entry} | PnL: ${pnl}")
            
    except Exception as e:
        print(f" Erro ao ler posições: {e}")

    # 3. Checar Ordens Abertas
    try:
        orders = transport.get_open_orders()
        print(f"\n⏳ ORDENS ABERTAS ({len(orders)}):")
        if not orders:
            print("   (Nenhuma ordem pendente)")
        
        for o in orders:
            symbol = o.get('symbol')
            side = o.get('side')
            price = o.get('price')
            qty = o.get('quantity')
            print(f"    {symbol:<15} | {side:<5} | Qty: {qty} | Price: {price}")
            
    except Exception as e:
        print(f" Erro ao ler ordens: {e}")

if __name__ == "__main__":
    asyncio.run(check_status())
