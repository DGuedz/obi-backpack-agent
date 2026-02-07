import sys

def calculate_breakeven_roi():
    # Taxas Backpack (Taker)
    # Taker Fee: 0.06% (0.0006) por perna (Entrada + Saída)
    # Total Fee Roundtrip: 0.12% (0.0012)
    taker_fee = 0.0006
    roundtrip_fee = taker_fee * 2
    
    # Spread Médio (Estimado)
    # BTC Spread ~0.01%
    # Altcoins Spread ~0.02-0.05%
    spread_btc = 0.0001
    spread_alt = 0.0005
    
    # Lucro Mínimo Desejado (Centavo)
    # Se notional é $20 (10x alavancagem de $2)
    # $0.05 de lucro = 0.25% ROI
    
    # ROI Mínimo para "Sair no Zero" (Pagar Taxas + Spread)
    min_roi_btc = roundtrip_fee + spread_btc
    min_roi_alt = roundtrip_fee + spread_alt
    
    # ROI Mínimo para Lucro Real (Micro-Scalp)
    # Buffer de lucro: 0.1%
    target_roi_btc = min_roi_btc + 0.001
    target_roi_alt = min_roi_alt + 0.001
    
    print("\n MATEMÁTICA DO CENTAVO (SCALP SUSTENTÁVEL)")
    print("-" * 50)
    print(f"Taxa Total (Ida e Volta): {roundtrip_fee*100:.2f}%")
    print("-" * 50)
    print(f"BTC/ETH (Alta Liquidez):")
    print(f"   Custo (Taxa + Spread): {min_roi_btc*100:.2f}%")
    print(f"   ALVO MÍNIMO (Lucro):   {target_roi_btc*100:.2f}% (ROI)")
    print("-" * 50)
    print(f"ALTCOINS (FOGO, DOGE):")
    print(f"   Custo (Taxa + Spread): {min_roi_alt*100:.2f}%")
    print(f"   ALVO MÍNIMO (Lucro):   {target_roi_alt*100:.2f}% (ROI)")
    print("-" * 50)
    print(" CONCLUSÃO:")
    print("   Para encher o caixa centavo a centavo, precisamos sair com:")
    print("   ROI > 0.23% em Majors")
    print("   ROI > 0.30% em Altcoins")

calculate_breakeven_roi()
