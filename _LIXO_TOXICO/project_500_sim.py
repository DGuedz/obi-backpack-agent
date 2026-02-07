#!/usr/bin/env python3
"""
 PROJECT 500 - SIMULADOR DE CENÁRIOS FUTUROS
Objetivo: Traçar a rota matemática para transformar o capital atual (~$335) em $500.
Baseado em dados reais do Harvester Bot e Sentinel Protocol.
"""

def simulate_growth(initial_capital, daily_trades, win_rate, avg_profit_pct, avg_loss_pct, days):
    capital = initial_capital
    history = [capital]
    
    for day in range(days):
        daily_pnl = 0
        for _ in range(daily_trades):
            # Simulação Probabilística Simplificada (Valor Esperado)
            # EV = (WinRate * Profit) - (LossRate * Loss)
            # Harvester tem WinRate alto por buscar scalps curtos e usar Sentinel Breakeven
            
            # Ajuste de "Realidade": Nem todo trade executa
            trade_allocation = 50.0 # $50 por slot
            
            # Resultado ponderado do trade
            outcome = (win_rate * (trade_allocation * avg_profit_pct)) - ((1 - win_rate) * (trade_allocation * avg_loss_pct))
            daily_pnl += outcome
            
        capital += daily_pnl
        history.append(capital)
        
    return history

def run_simulation():
    CURRENT_CAPITAL = 462.44 # Capital Atualizado (Main + LFG)
    TARGET_CAPITAL = 500.0
    
    print(f" PROJECT 500: Rota para a Recuperação (CAPITAL TURBINADO)")
    print(f"   Capital Inicial: ${CURRENT_CAPITAL:.2f}")
    print(f"   Alvo: ${TARGET_CAPITAL:.2f}")
    print(f"   Gap: ${TARGET_CAPITAL - CURRENT_CAPITAL:.2f}")
    print("-" * 40)

    # --- CENÁRIO 1: CONSERVADOR (Modo Guerrilha/Sentinel) ---
    c1_days = 0
    c1_cap = CURRENT_CAPITAL
    while c1_cap < TARGET_CAPITAL:
        c1_days += 1
        daily_gain = 5 * ((0.70 * (50 * 0.006)) - (0.30 * (50 * 0.01)))
        c1_cap += daily_gain
        if c1_days > 365: break 

    print(f"\n CENÁRIO 1: O CAMINHO SEGURO (Conservador)")
    print(f"   Estratégia: Sniper/Guerrilla")
    print(f"   Trades/Dia: 5 | WinRate: 70%")
    print(f"   Meta Diária: ~${(c1_cap - CURRENT_CAPITAL)/c1_days:.2f}")
    print(f"   Tempo Estimado: {c1_days} dias")
    
    # --- CENÁRIO 2: AGRESSIVO (Harvester Full Force) ---
    c2_days = 0
    c2_cap = CURRENT_CAPITAL
    while c2_cap < TARGET_CAPITAL:
        c2_days += 1
        # Com mais capital, podemos usar mais slots. 
        # Capital livre ~$460. Podemos usar 6 slots de $50 = $300 em jogo.
        daily_gain = 10 * ((0.75 * (50 * 0.008)) - (0.25 * (50 * 0.015)))
        c2_cap += daily_gain
        if c2_days > 365: break

    print(f"\n CENÁRIO 2: A COLHEITA INTENSIVA (Agressivo)")
    print(f"   Estratégia: Harvester V3 (6 Slots)")
    print(f"   Trades/Dia: 10 (Alta Qualidade) | WinRate: 75%")
    print(f"   Meta Diária: ~${(c2_cap - CURRENT_CAPITAL)/c2_days:.2f}")
    print(f"   Tempo Estimado: {c2_days} dias")
    print(f"   Risco: MÉDIO (Exige monitoramento constante do Brain)")

    print("-" * 40)
    print(" CONCLUSÃO TÁTICA:")
    if c2_days < c1_days:
        print(f"   Aceleramos {c1_days - c2_days} dias usando o Harvester.")
        print("   Recomendação: Manter Harvester ligado mas sob vigilância do Sentinel.")
    else:
        print("   A pressa é inimiga da perfeição. O modo Conservador é matematicamente superior.")

if __name__ == "__main__":
    run_simulation()
