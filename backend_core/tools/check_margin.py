import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport
from risk_manager import RiskManager

async def check_margin():
    load_dotenv()
    print("\n VERIFICANDO CAPACIDADE DE MARGEM...")
    
    transport = BackpackTransport()
    risk = RiskManager(transport)
    
    collateral = transport.get_account_collateral()
    if not collateral:
        print(" Erro ao obter dados da conta.")
        return

    equity = float(collateral.get('netEquity', 0))
    available = float(collateral.get('netEquityAvailable', 0))
    used = equity - available
    
    # Regra 70/30
    reserve = equity * 0.30
    max_operable = equity * 0.70
    current_operable = max(0, max_operable - used)
    
    print("-" * 50)
    print(f" Equity Total:       ${equity:.2f}")
    print(f" Reserva (30%):      ${reserve:.2f}")
    print(f" Teto Operacional:   ${max_operable:.2f}")
    print(f" Capital Em Uso:     ${used:.2f} ({(used/equity)*100:.1f}%)")
    print(f" Disponível (Real):  ${current_operable:.2f}")
    print("-" * 50)
    
    # Capacidade de Slots (Considerando $100 de margem por trade base)
    slots = int(current_operable / 50) # $50 de margem mínima por trade
    print(f" Capacidade Estimada de Novos Trades: {slots} (Base $50 margem)")
    
    if slots > 0:
        print(" PODEMOS ABRIR NOVAS POSIÇÕES.")
    else:
        print("️ MARGEM NO LIMITE DA REGRA 70/30. NÃO ABRIR NOVAS POSIÇÕES.")

if __name__ == "__main__":
    asyncio.run(check_margin())
