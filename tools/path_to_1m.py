import os
import sys
import asyncio
from dotenv import load_dotenv
import pandas as pd

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from risk_manager import RiskManager

async def calculate_path_to_million():
    load_dotenv()
    
    print("\n CALCULADORA DE VOLUME FARMING: RUMO A $1M")
    print("=" * 60)
    
    transport = BackpackTransport()
    
    # 1. Obter Capital Real
    balance = transport.get_account_collateral() # Correct method for equity/collateral
    usdc_balance = 0
    
    # Backpack Collateral API returns list or dict? Usually dict with 'assets' or direct fields
    # Need to handle structure based on known API
    # Assuming standard structure or simulating if empty
    
    if balance and 'assets' in balance:
         for asset in balance['assets']:
             if asset['symbol'] == 'USDC':
                 usdc_balance = float(asset.get('available', 0)) + float(asset.get('locked', 0))
                 break
    elif balance and 'totalEquity' in balance: # Sometimes returns equity directly
        usdc_balance = float(balance['totalEquity'])

    # Mock para teste se API falhar ou estiver zerada (assumindo capital da HYPE liberado)
    if usdc_balance < 10:
        print(f"️ Saldo detectado baixo (${usdc_balance:.2f}). Simulando com capital estimado de $600.")
        capital = 600.0
    else:
        capital = usdc_balance
        
    print(f" Capital Base (Equity): ${capital:.2f}")
    print(f" Meta de Volume:       $1,000,000.00")
    print(f"⏳ Tempo Restante:       24 Horas")
    print("-" * 60)
    
    scenarios = [5, 10, 20, 50]
    results = []
    
    for lev in scenarios:
        # Tamanho da Posição (Notional)
        position_size = capital * lev
        
        # Volume por Trade Completo (Entrada + Saída)
        vol_per_trade = position_size * 2
        
        # Trades Necessários
        trades_needed = 1_000_000 / vol_per_trade
        
        # Frequência (Trades por Hora)
        trades_per_hour = trades_needed / 24
        
        # Risco de Taxas (Taker 0.05% vs Maker 0.02% Rebate estimativo)
        # Pior caso: Taker na Entrada e Saída
        taker_cost = 1_000_000 * 0.0005 
        # Melhor caso: Maker na Entrada e Saída (Zero ou Rebate)
        maker_cost = 0 # Assumindo 0 para simplificar, mas pode ser lucro
        
        results.append({
            "Lev (x)": lev,
            "Pos Size ($)": f"${position_size:,.0f}",
            "Vol/Round ($)": f"${vol_per_trade:,.0f}",
            "Trades Total": int(trades_needed + 1),
            "Trades/Hora": f"{trades_per_hour:.1f}",
            "Custo Taker": f"${taker_cost:.0f} (️)",
            "Viabilidade": "" if trades_per_hour < 10 else "️ Hard" if trades_per_hour < 30 else " Insano"
        })
        
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print("=" * 60)
    print("\n CONCLUSÃO DO ESTUDO:")
    print("1. PROIBIDO TAKER: Pagar taxas ($500) quebraria a banca.")
    print("2. ALAVANCAGEM: Com 10x, precisamos de ~3.5 trades/hora. Doável.")
    print("3. ATIVO: BTC_USDC_PERP (Spread menor facilita sair no 0x0 Maker).")
    print("4. RISCO: Em 20x/50x, um candle de 1% liquida a conta. 10x é o teto racional.")

if __name__ == "__main__":
    asyncio.run(calculate_path_to_million())