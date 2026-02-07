import sys

def analyze_50x_strategy(margin_usd=3.0, leverage=50, taker_fee_rate=0.00085): # 0.085% taker fee estimate (standard)
    print("\n ANÁLISE DE VIABILIDADE: ESTRATÉGIA 50x MICRO SCALP")
    print("=" * 60)
    
    notional_position = margin_usd * leverage
    print(f" Margem Inicial: ${margin_usd:.2f}")
    print(f" Alavancagem: {leverage}x")
    print(f" Tamanho da Posição (Notional): ${notional_position:.2f}")
    
    # Fee Calculation (Roundtrip Taker)
    # Fee is calculated on Notional Size
    entry_fee = notional_position * taker_fee_rate
    exit_fee = notional_position * taker_fee_rate # Assuming exit at same price for breakeven calc
    total_fees = entry_fee + exit_fee
    
    print(f"\n Custo de Taxas (Taker/Taker Roundtrip):")
    print(f"   - Entrada: ${entry_fee:.4f}")
    print(f"   - Saída:   ${exit_fee:.4f}")
    print(f"   - TOTAL:   ${total_fees:.4f} (Isso sai do seu lucro!)")
    
    # Breakeven Calculation
    # Quanto o preço precisa mover a favor SÓ para pagar as taxas?
    # Required Profit = Total Fees
    # Price Move % = Total Fees / Notional
    breakeven_move_pct = (total_fees / notional_position) * 100
    
    print(f"\n️ PONTO DE EQUILÍBRIO (BREAKEVEN):")
    print(f"   O preço precisa mover {breakeven_move_pct:.4f}% a seu favor APENAS para pagar as taxas.")
    print(f"   Em BTC ($96,000), isso é um movimento de ~${(96000 * breakeven_move_pct/100):.2f}")
    
    # Profit Scenarios
    print(f"\n CENÁRIOS DE LUCRO (Líquido de Taxas):")
    moves = [0.2, 0.3, 0.5, 1.0] # % Price Move
    for move in moves:
        gross_profit = notional_position * (move / 100)
        net_profit = gross_profit - total_fees
        roi_margin = (net_profit / margin_usd) * 100
        print(f"   - Movimento {move}%: Lucro Bruto ${gross_profit:.2f} | Líquido ${net_profit:.2f} ({roi_margin:.1f}% ROI)")

    # Risk Scenarios
    print(f"\n️ RISCO DE LIQUIDAÇÃO:")
    # Liquidation usually at Maintenance Margin (approx 0.5% or 1% depending on exchange)
    # At 50x, Initial Margin is 2%. Maintenance is likely ~1%.
    # So you have ~1% buffer before liquidation.
    liq_move = 1.0 # Rough estimate for 50x
    print(f"   Com 50x, um movimento de ~{liq_move}% contra você LIQUIDA a posição.")
    print(f"   Perda Máxima: ${margin_usd:.2f} (100% da margem)")

    print("\n CONCLUSÃO TÉCNICA:")
    if breakeven_move_pct > 0.15:
         print("   ️ ALERTA: Custo Taker/Taker é ALTO para Scalp Curto.")
         print("   Sugerimos Tentar MAKER na Saída (Limit Order) para reduzir custo pela metade.")
    else:
         print("    Viável para movimentos de volatilidade média (>0.3%).")

if __name__ == "__main__":
    analyze_50x_strategy()
