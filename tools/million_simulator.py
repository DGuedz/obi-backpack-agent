import random
import pandas as pd

def simulate_million_run():
    print("\n MONTE CARLO: O CAMINHO DO MILHÃO")
    print("=" * 60)
    
    # Parâmetros Reais
    capital_inicial = 600.0
    alavancagem = 10
    notional = capital_inicial * alavancagem # $6.000
    volume_por_trade = notional * 2 # $12.000 (Entrada + Saída)
    trades_necessarios = 1_000_000 / volume_por_trade # ~84 trades
    
    # Payoff (Maker vs Taker Stop)
    tp_pct = 0.0009 # +0.09% (Spread + Rebate)
    sl_pct = 0.0055 # -0.55% (Stop + Taxa Taker)
    
    win_profit = notional * tp_pct # ~$5.40
    loss_value = notional * sl_pct # ~$33.00
    
    print(f" Capital: ${capital_inicial:.2f} | Lev: {alavancagem}x")
    print(f" Meta Volume: $1M ({int(trades_necessarios)} trades)")
    print(f" Win (TP Maker): +${win_profit:.2f} (+0.09%)")
    print(f" Loss (SL Taker): -${loss_value:.2f} (-0.55%)")
    print(f"️ Risco/Retorno: 1:{loss_value/win_profit:.1f} (Precisamos de alta taxa de acerto!)")
    print("-" * 60)
    
    # Simulação de Cenários de Win Rate
    scenarios = [50, 70, 80, 85, 90, 95]
    results = []
    
    for win_rate in scenarios:
        capital = capital_inicial
        wins = 0
        losses = 0
        broken = False
        
        for _ in range(int(trades_necessarios)):
            if random.random() * 100 < win_rate:
                capital += win_profit
                wins += 1
            else:
                capital -= loss_value
                losses += 1
            
            if capital <= 50: # Ruína
                broken = True
                break
        
        status = " QUEBROU" if broken else f" ${capital:.2f}"
        pnl = capital - capital_inicial
        
        results.append({
            "Win Rate %": f"{win_rate}%",
            "Resultado Final": status,
            "PnL Líquido": f"${pnl:.2f}",
            "Wins/Losses": f"{wins}/{losses}"
        })
        
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print("=" * 60)
    
    # Cálculo do Breakeven Rate
    # Win * Profit = Loss * Loss_Value
    # WR * 5.4 = (1-WR) * 33
    # 5.4WR = 33 - 33WR
    # 38.4WR = 33
    # WR = 33/38.4 = 0.86
    
    be_rate = (loss_value / (win_profit + loss_value)) * 100
    print(f" WIN RATE MÍNIMO PARA SOBREVIVER: {be_rate:.1f}%")
    print(f"   -> Com TP curto e SL longo, precisamos acertar MUITO.")
    print(f"   -> A 'Cerca Elétrica' (Straddle) deve garantir >90% de acerto no Maker.")

if __name__ == "__main__":
    simulate_million_run()