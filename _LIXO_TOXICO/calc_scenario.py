
def calc_scenario():
    # Parâmetros
    leverage = 10
    margin = 100
    notional = 1000
    
    entry_price = 2.5737 # Preço aproximado da sua entrada Short a mercado
    current_price = 2.6155 # Preço atual do repique (negativo para você que está Short)
    
    # Se você entrou em 2.57 e está em 2.61, você está NEGATIVO.
    # Short: Ganha se preço cair.
    
    price_move_pct = (current_price - entry_price) / entry_price
    pnl_raw = -price_move_pct * notional # Negativo pois subiu
    
    fees_open = notional * 0.00085 # 0.85
    fees_close = notional * 0.00085 # 0.85 (estimado market)
    total_fees = fees_open + fees_close
    
    net_pnl = pnl_raw - total_fees
    
    print(f" CENÁRIO ATUAL (SHORT em {entry_price}):")
    print(f"   Preço Atual: {current_price}")
    print(f"   Variação: +{price_move_pct*100:.2f}% (Contra você)")
    print(f"   PnL Bruto: ${pnl_raw:.2f}")
    print(f"   Taxas: ${total_fees:.2f}")
    print(f"   PnL Líquido: ${net_pnl:.2f}")
    
    # Possibilidade de Ganho (Se cair para o fundo 2.41)
    target_price = 2.41
    potential_move = (entry_price - target_price) / entry_price
    potential_profit = potential_move * notional
    net_potential = potential_profit - total_fees
    
    print(f"\n POTENCIAL (Se voltar ao fundo 2.41):")
    print(f"   Alvo: {target_price}")
    print(f"   Lucro Previsto: ${net_potential:.2f} (+{net_potential/margin*100:.1f}% ROI)")

if __name__ == "__main__":
    calc_scenario()
