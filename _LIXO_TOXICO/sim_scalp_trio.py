#!/usr/bin/env python3
"""
 SIM SCALP TRIO - High Frequency Simulation
Simula 3 operações simultâneas com $20 cada (5x Lev).
Calcula PnL líquido, Taxas e Probabilidade baseada no Book.
"""

import time
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from market_intelligence import MarketIntelligence
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração
MARGIN_PER_TRADE = 20.0
LEVERAGE = 5
NOTIONAL = MARGIN_PER_TRADE * LEVERAGE # $100
SL_PCT = 0.02 # 2%
TP_PCT = 0.04 # 4% (Risco:Retorno 1:2)
FEE_RATE = 0.00085 # 0.085% Taker (Pior caso)

ASSETS = ["SOL_USDC_PERP", "ETH_USDC_PERP", "WIF_USDC_PERP"]

def simulate():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    mi = MarketIntelligence()
    
    print(f"\n SIMULAÇÃO DE SCALP TRIO (Margem: ${MARGIN_PER_TRADE} | Lev: {LEVERAGE}x)")
    print(f"   Alvo: +{TP_PCT*100}% | Stop: -{SL_PCT*100}% | Size: ${NOTIONAL}")
    print("-" * 95)
    print(f"{'ASSET':<10} | {'PRICE':<10} | {'ENTRY':<10} | {'STOP ($)':<10} | {'TARGET ($)':<10} | {'NET PROFIT':<10} | {'VIABILITY'}")
    print("-" * 95)
    
    total_potential_profit = 0
    total_potential_loss = 0
    
    for symbol in ASSETS:
        try:
            # 1. Dados de Mercado em Tempo Real
            ticker = data.get_ticker(symbol)
            price = float(ticker['lastPrice'])
            
            # 2. Inteligência (Direção)
            analysis = mi.analyze_market_regime(symbol)
            direction = "LONG" # Default para simulação de recuperação
            if analysis and analysis['score'] < -2: direction = "SHORT"
            
            # 3. Cálculos de Preço
            if direction == "LONG":
                sl_price = price * (1 - SL_PCT)
                tp_price = price * (1 + TP_PCT)
            else:
                sl_price = price * (1 + SL_PCT)
                tp_price = price * (1 - TP_PCT)
                
            # 4. Cálculos Financeiros
            gross_profit = NOTIONAL * TP_PCT
            gross_loss = NOTIONAL * SL_PCT
            
            # Taxas (Entrada Taker + Saída Taker - Pior Caso)
            fees = (NOTIONAL * FEE_RATE) + (NOTIONAL * (1+TP_PCT) * FEE_RATE)
            
            net_profit = gross_profit - fees
            net_loss = gross_loss + fees # Prejuízo aumenta com taxas
            
            # Viabilidade (Book Imbalance ajuda?)
            viability = " GO"
            if analysis['risk'] == "HIGH": viability = "️ RISKY"
            if direction == "LONG" and analysis['rsi'] > 70: viability = " NO (Topo)"
            if direction == "SHORT" and analysis['rsi'] < 30: viability = " NO (Fundo)"
            
            # Output
            print(f"{symbol.split('_')[0]:<10} | ${price:<9.2f} | {direction:<10} | -${net_loss:.2f}    | +${net_profit:.2f}    | +{((net_profit/MARGIN_PER_TRADE)*100):.1f}%     | {viability}")
            
            if "GO" in viability:
                total_potential_profit += net_profit
                total_potential_loss += net_loss
                
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
            
    print("-" * 95)
    print(f" CENÁRIO OTIMISTA (3 Wins): +${total_potential_profit:.2f} (ROI: +{(total_potential_profit/60)*100:.1f}%)")
    print(f"️ CENÁRIO REALISTA (1 Win / 2 Loss): ${total_potential_profit - (2 * (NOTIONAL * SL_PCT + fees)):.2f}")
    print(f" CENÁRIO PESSIMISTA (3 Loss): -${(total_potential_loss * 3) / 3:.2f} (Total: -${total_potential_loss:.2f})")

if __name__ == "__main__":
    simulate()