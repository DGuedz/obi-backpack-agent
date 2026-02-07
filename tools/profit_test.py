import sys
import os

# Simulação de Custos e Lucros
# Objetivo: Calcular a alavancagem ideal para ganho sustentável.

def calculate_scenario(leverage, capital, target_roe, maker_fee=0.0002, taker_fee=0.0005, sl_pct=0.015):
    """
    Calcula os números para um cenário de alavancagem.
    
    Args:
        leverage (int): Alavancagem (ex: 10, 20, 50).
        capital (float): Capital por trade (Margem).
        target_roe (float): ROE Alvo (ex: 0.05 para 5%).
        maker_fee (float): Taxa Maker (Backpack ~0.02%).
        taker_fee (float): Taxa Taker (Backpack ~0.05%).
        sl_pct (float): Distância do Stop Loss em % do preço (ex: 1.5%).
    """
    notional = capital * leverage
    
    # 1. Movimento de Preço Necessário para o Alvo
    # ROE = (PriceDelta% * Leverage)
    # PriceDelta% = ROE / Leverage
    price_move_needed_pct = target_roe / leverage
    
    # 2. Custos (Fees)
    # Entry (Maker)
    entry_fee = notional * maker_fee
    
    # Exit (Maker - Ideal)
    exit_fee_maker = notional * maker_fee
    
    # Exit (Taker - Stop Loss ou Panic)
    exit_fee_taker = notional * taker_fee
    
    # 3. Lucro Bruto vs Líquido
    gross_profit = notional * price_move_needed_pct # Deve ser igual a capital * target_roe
    
    net_profit_maker = gross_profit - (entry_fee + exit_fee_maker)
    net_profit_taker = gross_profit - (entry_fee + exit_fee_taker) # Se sair a mercado no lucro (raro, mas possível)
    
    # 4. Stop Loss Impact
    # Perda Bruta no SL
    gross_loss_sl = notional * sl_pct
    total_loss_sl = gross_loss_sl + entry_fee + exit_fee_taker
    
    # Breakeven (Price Move para pagar taxas)
    # Fees Total (Maker Entry + Maker Exit)
    total_fees_maker = entry_fee + exit_fee_maker
    breakeven_move_pct = total_fees_maker / notional
    
    return {
        "leverage": leverage,
        "notional": notional,
        "price_move_needed": price_move_needed_pct * 100, # %
        "breakeven_move": breakeven_move_pct * 100, # %
        "gross_profit": gross_profit,
        "net_profit": net_profit_maker,
        "fees_impact_pct": (total_fees_maker / gross_profit) * 100 if gross_profit > 0 else 0,
        "sl_loss": total_loss_sl,
        "risk_reward": net_profit_maker / total_loss_sl if total_loss_sl > 0 else 0
    }

def run_simulation():
    capital = 20.0 # $20 por trade (exemplo conservador para teste)
    target_roe = 0.05 # 5% de ROE por trade (Meta de Scalp)
    
    print(f"\n SIMULAÇÃO DE VIABILIDADE (Capital Base: ${capital:.2f} | Meta ROE: {target_roe*100}%)")
    print(f"{'LEV':<5} | {'NOTIONAL':<10} | {'MOVE %':<10} | {'BREAKEVEN':<10} | {'LUCRO LÍQ':<10} | {'RISCO SL':<10} | {'R:R':<5}")
    print("-" * 85)
    
    scenarios = [5, 10, 20, 50, 75]
    
    best_scenario = None
    best_score = -999
    
    for lev in scenarios:
        res = calculate_scenario(lev, capital, target_roe)
        
        # Score simples: Lucro Liquido / Risco (Risk Adjusted Return)
        # Penaliza alavancagem excessiva se o movimento necessário for muito pequeno (ruído)
        # Mas aqui o foco é matemático.
        
        print(f"{res['leverage']}x   | ${res['notional']:<9.2f} | {res['price_move_needed']:<8.4f}% | {res['breakeven_move']:<8.4f}% | ${res['net_profit']:<9.2f} | ${res['sl_loss']:<9.2f} | {res['risk_reward']:.2f}")
        
        if res['risk_reward'] > best_score:
            best_score = res['risk_reward']
            best_scenario = res
            
    print("-" * 85)
    print(f" Veredito Matemático:")
    print(f"A alavancagem de {best_scenario['leverage']}x oferece o melhor Retorno Ajustado ao Risco.")
    print(f"Para lucrar ${best_scenario['net_profit']:.2f} (Líquido), o preço só precisa mover {best_scenario['price_move_needed']:.4f}%.")
    print(f"O custo operacional (Taxas) consome {best_scenario['fees_impact_pct']:.1f}% do lucro bruto.")
    
    if best_scenario['leverage'] >= 50:
        print("\n️ ALERTA: Alavancagem > 50x é perigosa para 'Ganho Sustentável'. Recomendo limitar a 20x.")
    elif best_scenario['leverage'] <= 10:
        print("\n SEGURO: Alavancagem conservadora. Ideal para reconstrução de capital ('Voltar aos 300').")
        
    return best_scenario['leverage']

if __name__ == "__main__":
    run_simulation()
