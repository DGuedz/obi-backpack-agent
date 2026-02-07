import sys

def calculate_kpi():
    print("\n CALCULADORA DE DESEMPENHO & PROJEÇÃO (OBI WORK)\n")
    
    # Check for args
    if len(sys.argv) > 1:
        current_capital = float(sys.argv[1])
        daily_volume_target = float(sys.argv[2])
        win_rate_target = float(sys.argv[3])
    else:
        try:
            current_capital = float(input(" Capital Atual ($): "))
            daily_volume_target = float(input(" Meta de Volume Diário ($): "))
            win_rate_target = float(input(" Win Rate Alvo (%): "))
        except ValueError:
            print(" Entrada inválida. Usando valores padrão.")
            current_capital = 300.0
            daily_volume_target = 38000.0 # Based on recent report
            win_rate_target = 60.0
            
    win_rate_target /= 100
    avg_rr = 1.5
    trades_per_day = 20

    print("\n--- PROJEÇÃO MENSAL (30 Dias) ---")
    
    # Assumptions
    risk_per_trade_pct = 0.01 # 1% Risk
    risk_amount = current_capital * risk_per_trade_pct
    reward_amount = risk_amount * avg_rr
    
    daily_wins = trades_per_day * win_rate_target
    daily_losses = trades_per_day * (1 - win_rate_target)
    
    daily_pnl = (daily_wins * reward_amount) - (daily_losses * risk_amount)
    monthly_pnl = daily_pnl * 30
    
    projected_capital = current_capital + monthly_pnl
    total_monthly_volume = daily_volume_target * 30
    
    # Fee Estimation (Taker 0.05% worst case, Maker 0.02%)
    # Assuming mix, say 0.04% avg
    est_fees = total_monthly_volume * 0.0004
    net_monthly_pnl = monthly_pnl - est_fees
    
    print(f" Crescimento de Capital:")
    print(f"   - Inicial: ${current_capital:,.2f}")
    print(f"   - PnL Bruto Projetado: ${monthly_pnl:,.2f}")
    print(f"   - Taxas Estimadas: -${est_fees:,.2f}")
    print(f"   - PnL Líquido: ${net_monthly_pnl:,.2f}")
    print(f"   - Final Projetado: ${current_capital + net_monthly_pnl:,.2f}")
    
    print(f"\n Projeção Backpack:")
    print(f"   - Volume Mensal: ${total_monthly_volume:,.2f}")
    print(f"   - Status Tier: Provável manutenção de Gold/Platinum se mantiver esse ritmo.")
    
    print(f"\n️ Requisito para Sucesso:")
    print(f"   - Você precisa de {daily_wins:.1f} wins contra {daily_losses:.1f} loss por dia.")
    print(f"   - O protocolo Ironclad deve garantir esse Win Rate > {win_rate_target*100}%.")

if __name__ == "__main__":
    calculate_kpi()
