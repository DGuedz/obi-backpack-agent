import sys
import os
from dotenv import load_dotenv

# Path setup
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

# Simple projection
def calc_feasibility():
    print(" CALCULADORA DE VIABILIDADE - MISSÃO 1 MILHÃO S4")
    print("-" * 50)
    
    # Inputs (Estimados do último log)
    capital = 90.0 # Aproximado do log noturno
    target_volume = 1_000_000 # 1 Milhão
    remaining_days = 1 # Último dia
    
    # Parâmetros Operacionais (High Frequency)
    leverage = 20 # S4 Finale precisa ser agressivo
    trade_size = capital * leverage # $90 * 20 = $1800 Notional
    
    # Quantos trades?
    trades_needed = target_volume / trade_size
    
    # Tempo
    hours_available = 24
    minutes_available = hours_available * 60
    trades_per_hour = trades_needed / hours_available
    trades_per_minute = trades_needed / minutes_available
    
    # Custos (Taker 0.08% approx se não tiver rebate)
    # Volume * Fee Rate
    estimated_fees = target_volume * 0.0008 
    
    print(f" Capital Inicial: ${capital}")
    print(f" Meta de Volume: ${target_volume:,.2f}")
    print(f" Alavancagem: {leverage}x")
    print(f" Tamanho por Trade (Notional): ${trade_size:,.2f}")
    print("-" * 50)
    print(f" Trades Necessários: {trades_needed:.0f}")
    print(f"⏱️ Ritmo Necessário: {trades_per_hour:.0f} trades/hora ({trades_per_minute:.1f} trades/min)")
    print(f" Custo Estimado (Fees): ${estimated_fees:,.2f}")
    print("-" * 50)
    
    if estimated_fees > capital:
        print(" IMPOSSÍVEL MATEMATICAMENTE: As taxas ($" + f"{estimated_fees:.2f}" + ") consumiriam todo o capital ($" + f"{capital}" + ").")
        print(" SOLUÇÃO: Precisamos de MAKER ORDERS (Rebate) ou injetar capital.")
    else:
        print("️ RISCO EXTREMO: Viável apenas com taxa de acerto > 90% para cobrir custos.")

if __name__ == "__main__":
    calc_feasibility()
