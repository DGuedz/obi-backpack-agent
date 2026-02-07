import pandas as pd

def simulate_taker_vs_maker():
    print(" SIMULAÇÃO: MAKER (BALEIA) vs TAKER (SARDINHA)")
    print("================================================")
    print("Cenário: Capital $1,000 | Alavancagem 10x | Volume $10,000 por Trade")
    print("Ativo: VOLATILE_COIN (Alta Volatilidade)")
    print("-" * 60)

    # Parâmetros
    trade_volume = 10000.0 # $10k Notional
    
    # Taxas Backpack (Taker vs Maker)
    # Taker: 0.055% (Padrão de mercado para sardinhas)
    # Maker: 0.02% (Backpack VIP ou Rebate) ou 0% se tiver volume.
    # Vamos ser realistas: 
    # Maker Fee: 0.02% (Pagamos pouco)
    # Taker Fee: 0.06% (Pagamos caro pela pressa)
    fee_maker = 0.0002 
    fee_taker = 0.0006 
    
    # Spread (Custo oculto do Taker)
    # Maker entra no Bid/Ask exato (Spread = 0)
    # Taker atravessa o spread (Spread = 0.05% médio)
    spread_cost = 0.0005 

    # Simulação de 1 Trade (Entrada + Saída)
    print("\n1. CUSTO POR TRADE (Entrada + Saída):")
    
    # --- TAKER (SARDINHA) ---
    # Paga taxa na entrada e na saída + Spread na entrada e saída
    taker_fees = (trade_volume * fee_taker) * 2 
    taker_spread = (trade_volume * spread_cost) * 2
    taker_total_cost = taker_fees + taker_spread
    
    print(f" TAKER (A Mercado):")
    print(f"   Taxas Corretora:  ${taker_fees:.2f}")
    print(f"   Custo Spread:     ${taker_spread:.2f}")
    print(f"    CUSTO TOTAL:   ${taker_total_cost:.2f} (Precisa lucrar > 0.11% só para empatar)")

    # --- MAKER (BALEIA) ---
    # Paga taxa reduzida e NÃO paga spread (ganha a fila)
    maker_fees = (trade_volume * fee_maker) * 2
    maker_spread = 0.0 # Maker não paga spread, ele É o spread
    maker_total_cost = maker_fees
    
    print(f"\n MAKER (Limit Post-Only):")
    print(f"   Taxas Corretora:  ${maker_fees:.2f}")
    print(f"   Custo Spread:     $0.00")
    print(f"   🟢 CUSTO TOTAL:   ${maker_total_cost:.2f} (Precisa lucrar > 0.04% para empatar)")

    print("-" * 60)
    
    # Simulação de 100 Trades (Meta do Farm)
    print("\n2. PROJEÇÃO DE 100 TRADES (Volume $1 Milhão):")
    
    total_vol = trade_volume * 100
    taker_burn = taker_total_cost * 100
    maker_burn = maker_total_cost * 100
    
    diff = taker_burn - maker_burn
    
    print(f" Taker Queima:     ${taker_burn:,.2f}")
    print(f" Maker Queima:     ${maker_burn:,.2f}")
    print(f" ECONOMIA REAL:    ${diff:,.2f}")
    
    print("-" * 60)
    print(" CONCLUSÃO DA EQUAÇÃO:")
    print("Para operar A MERCADO (Taker) com lucro seguro, precisamos de uma estratégia")
    print("que acerte movimentos maiores que 0.20% (Break-even + Lucro) com >60% de Winrate.")
    print("No Scalp de 5m, movimentos limpos >0.20% são raros e ruidosos.")
    print("\nVEREDITO: Operar Taker em Scalp é matematicamente insustentável no longo prazo.")
    print("A 'Equação Segura' para Taker exige Swing Trade (Alvos > 1%), não Scalp.")

if __name__ == "__main__":
    simulate_taker_vs_maker()