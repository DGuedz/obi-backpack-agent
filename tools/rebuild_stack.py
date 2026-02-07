import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def rebuild_stack():
    print("️ OPERAÇÃO REBUILD STACK (DOLLARIZATION)")
    print("=" * 60)
    load_dotenv()
    
    transport = BackpackTransport()
    
    # 1. Verificar Colateral (USDC)
    try:
        collateral = transport.get_account_collateral()
        equity = float(collateral.get('netEquity', 0))
        available = float(collateral.get('netEquityAvailable', 0))
        
        print(f" Equity Total:      ${equity:.2f}")
        print(f" Disponível (USDC): ${available:.2f}")
        
        if available < equity * 0.99:
            print("️ AVISO: Parte do capital ainda está travado em margem ou ordens.")
        else:
            print(" CAPITAL 100% LÍQUIDO EM DÓLAR (USDC).")
            
    except Exception as e:
        print(f" Erro ao ler colateral: {e}")

    # 2. Confirmar Posições Zeradas
    try:
        positions = transport.get_positions()
        active_pos = [p for p in positions if float(p.get('quantity', 0)) != 0]
        
        if active_pos:
            print(f"\n ATENÇÃO: {len(active_pos)} POSIÇÕES AINDA ABERTAS!")
            for p in active_pos:
                print(f"   • {p.get('symbol')} ({p.get('side')}): {p.get('quantity')}")
        else:
            print("\n POSIÇÕES: TODAS ZERADAS.")
            
    except Exception as e:
        print(f" Erro ao ler posições: {e}")
        
    # 3. Confirmar Ordens Zeradas
    try:
        orders = transport.get_open_orders()
        if orders:
            print(f"\n ATENÇÃO: {len(orders)} ORDENS PENDENTES!")
        else:
            print("\n ORDENS: MESA LIMPA.")
            
    except Exception as e:
        print(f" Erro ao ler ordens: {e}")
        
    print("\n NOVO MODO ATIVADO: ASYMMETRIC_PROFIT")
    print("=" * 60)
    print("   • OBI Threshold:  0.35 (Só entra com fluxo massivo)")
    print("   • Alavancagem:    3x (Anti-Liquidação)")
    print("   • Target Profit:  15% (Busca de Tendência)")
    print("   • Filosofia:      Sniper de Elite. 1 Tiro, 1 Morte.")
    print("\nPronto para iniciar a reconstrução do stack financeiro.")

if __name__ == "__main__":
    asyncio.run(rebuild_stack())
