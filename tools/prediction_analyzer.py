
import sys

def calculate_prediction_metrics(yes_price, no_price, estimated_true_prob=None, bankroll=1000):
    """
    Calcula métricas fundamentais para mercados de predição.
    
    Args:
        yes_price (float): Preço da ação 'Sim' (ex: 0.45 para 45%)
        no_price (float): Preço da ação 'Não' (ex: 0.55)
        estimated_true_prob (float, optional): Probabilidade real estimada (0.0 a 1.0)
        bankroll (float): Tamanho da banca para cálculo de Kelly
    """
    print(f"\n ANÁLISE DE MERCADO DE PREDIÇÃO")
    print(f"   Preço YES: {yes_price:.2f} | Preço NO: {no_price:.2f}")
    
    # 1. Market Structure (Vig/Overround)
    total_implied = yes_price + no_price
    vig = total_implied - 1.0
    
    print(f"\n1️⃣  ESTRUTURA DE MERCADO")
    print(f"   Probabilidade Implícita Total: {total_implied:.4f} (100% = 1.0)")
    if vig > 0:
        print(f"   ️ Vig (Taxa/Ineficiência): {vig*100:.2f}%")
        print(f"      (Você paga {vig*100:.2f}% extra 'para a casa' ou spread)")
    elif vig < 0:
        print(f"    ARBITRAGEM DETECTADA! (Soma < 1.0)")
        print(f"      Lucro Risk-Free: {abs(vig)*100:.2f}% comprando ambos!")
    else:
        print(f"    Mercado Perfeito (Soma = 1.0)")

    # 2. Fair Value (Normalized)
    fair_yes = yes_price / total_implied
    fair_no = no_price / total_implied
    print(f"\n2️⃣  PROBABILIDADE REAL IMPLÍCITA (Fair Value)")
    print(f"   YES: {fair_yes*100:.1f}%")
    print(f"   NO:  {fair_no*100:.1f}%")
    
    # 3. Edge Calculation (Se tiver estimativa)
    if estimated_true_prob is not None:
        print(f"\n3️⃣  CÁLCULO DE EDGE (Vantagem)")
        print(f"   Sua Estimativa: {estimated_true_prob*100:.1f}% para YES")
        
        # Kelly Criterion
        # f = (bp - q) / b
        # b = odds - 1 (decimal odds - 1). Em prediction (0-1), odds = 1/price
        # b = (1/price) - 1
        # p = estimated_true_prob
        # q = 1 - p
        
        if estimated_true_prob > fair_yes:
            print(f"    Vantagem no YES!")
            decimal_odds = 1 / yes_price
            b = decimal_odds - 1
            p = estimated_true_prob
            q = 1 - p
            
            kelly_f = (b * p - q) / b
            kelly_bet = kelly_f * bankroll
            
            print(f"      Decimal Odds: {decimal_odds:.2f}")
            print(f"      Kelly Fraction: {kelly_f*100:.2f}% da banca")
            print(f"      Aposta Sugerida: ${kelly_bet:.2f} (Full Kelly)")
            print(f"      Aposta Conservadora (Quarter Kelly): ${kelly_bet/4:.2f}")
            
        elif (1 - estimated_true_prob) > fair_no:
            print(f"    Vantagem no NO!")
            decimal_odds = 1 / no_price
            b = decimal_odds - 1
            p = 1 - estimated_true_prob # Prob de NO
            q = 1 - p
            
            kelly_f = (b * p - q) / b
            kelly_bet = kelly_f * bankroll
            
            print(f"      Decimal Odds: {decimal_odds:.2f}")
            print(f"      Kelly Fraction: {kelly_f*100:.2f}% da banca")
            print(f"      Aposta Sugerida: ${kelly_bet:.2f} (Full Kelly)")
            print(f"      Aposta Conservadora (Quarter Kelly): ${kelly_bet/4:.2f}")
        else:
            print(f"    Sem Edge (EV Negativo). Não aposte.")
            
    else:
        print("\n3️⃣  EDGE: Estimativa não fornecida.")
        print("   (Rode novamente fornecendo 'estimated_true_prob' para calcular Kelly)")

if __name__ == "__main__":
    # Exemplo simples interativo ou hardcoded para teste
    try:
        if len(sys.argv) > 2:
            y = float(sys.argv[1])
            n = float(sys.argv[2])
            p = float(sys.argv[3]) if len(sys.argv) > 3 else None
            calculate_prediction_metrics(y, n, p)
        else:
            print("Uso: python3 prediction_analyzer.py <yes_price> <no_price> [prob_estimada]")
            print("Exemplo: python3 prediction_analyzer.py 0.45 0.58 0.60")
            
            # Rodar exemplo padrão
            print("\n--- EXEMPLO DE EXECUÇÃO ---")
            calculate_prediction_metrics(0.40, 0.63, 0.50)
            
    except Exception as e:
        print(f"Erro: {e}")
