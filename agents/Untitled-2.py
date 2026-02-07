"""
SELEÇÃO_DE_ATIVOS_OTIMIZADA:
1. PRIORIDADE: Tokens com funding rate POSITIVO (long bias)
2. LIQUIDEZ: Volume 24h > $200M (avoid illiquid)
3. MOMENTUM: RSI(14) entre 40-60 (not overbought)
4. CORRELAÇÃO: >0.7 com BTC (follow lighthouse)
5. SETUP: Price > EMA20 (uptrend confirmation)
6. EXCLUSÃO: Avoid memecoins (high volatility risk)
"""