from market_intelligence import MarketIntelligence
import time

def scan():
    mi = MarketIntelligence()
    symbol = "ETH_USDC_PERP"
    print(f"\n RELATÓRIO DE INTELIGÊNCIA: {symbol}")
    print("-" * 50)
    
    analyses, score = mi.analyze_multi_timeframe(symbol)
    
    print("-" * 50)
    print(f" SCORE TOTAL DE CONFLUÊNCIA: {score}/12")
    
    if score >= 3:
        print(" DECISÃO: LONG SCALP (Forte)")
    elif score <= -3:
        print(" DECISÃO: SHORT SCALP (Forte)")
    else:
        print("️ DECISÃO: AGUARDAR (Neutro)")
        
    # Detalhes
    print("\n DETALHES TÉCNICOS:")
    for tf, data in analyses.items():
        rsi = data['rsi']
        price = data['price']
        bb_lower = data['bb_lower']
        bb_upper = data['bb_upper']
        
        status = "NEUTRO"
        if rsi < 40: status = "OVERSOLD (Bullish)"
        if rsi > 60: status = "TREND FORCE (Bullish)"
        
        if bb_lower > 0 and price <= bb_lower * 1.005: status += " + LIQ HUNT"
        
        print(f"   • {tf}: RSI {rsi:.1f} | ${price:.2f} | {status}")

if __name__ == "__main__":
    scan()
