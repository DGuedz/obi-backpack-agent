#!/usr/bin/env python3
"""
 RADAR SCAN - The Opportunity Hunter
Escaneia o mercado em busca de setups de Alta Probabilidade (TCP Compliant).
"""

import time
from market_intelligence import MarketIntelligence

# Lista de Ativos Líquidos na Backpack
ASSETS = [
    "SOL_USDC_PERP",
    "BTC_USDC_PERP",
    "ETH_USDC_PERP",
    "JUP_USDC_PERP",
    "WIF_USDC_PERP",
    "PYTH_USDC_PERP",
    "kBONK_USDC_PERP"
]

def scan_market():
    mi = MarketIntelligence()
    print("\n RADAR ATIVO: Escaneando Oportunidades...")
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'RSI':<5} | {'REGIME':<18} | {'RISK':<8} | {'SCORE'}")
    print("-" * 80)
    
    best_opportunity = None
    highest_score = -100
    
    for symbol in ASSETS:
        try:
            analysis = mi.analyze_market_regime(symbol)
            if not analysis: continue
            
            # Formatar Output
            risk_color = "🟢" if analysis['risk'] == "LOW" else ""
            score_color = "🟢" if analysis['score'] > 0 else ""
            rsi_val = f"{analysis['rsi']:.1f}"
            
            print(f"{symbol:<15} | ${analysis['price']:<9.4f} | {rsi_val:<5} | {analysis['regime']:<18} | {risk_color} {analysis['risk']:<5} | {score_color} {analysis['score']}")
            
            # Selecionar o melhor (em valor absoluto de tendência, mas com risco baixo)
            if analysis['risk'] == "LOW" and abs(analysis['score']) >= 2:
                # Priorizar maior score
                if abs(analysis['score']) > highest_score:
                    highest_score = abs(analysis['score'])
                    best_opportunity = analysis
                
        except Exception as e:
            print(f"️ Erro ao escanear {symbol}: {e}")
            
    print("-" * 80)
    
    if best_opportunity:
        direction = "LONG 🟢 (Oversold)" if best_opportunity['score'] > 0 else "SHORT  (Overbought)"
        print(f"\n OPORTUNIDADE SNIPER: {best_opportunity['symbol']}")
        print(f"   Direção: {direction}")
        print(f"   RSI: {best_opportunity['rsi']:.2f} | Imbalance: {best_opportunity['imbalance']:.2f}")
        print(f"   Setup: {best_opportunity['regime']}")
    else:
        print("\n Nenhuma assimetria perfeita encontrada. Aguardando RSI extremo.")

if __name__ == "__main__":
    scan_market()