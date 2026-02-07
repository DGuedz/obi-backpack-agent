import sys
import os
import time
import threading
import subprocess

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport
from tools import hyper_scalp_50x
from tools import maker_sniper_50x

# CONFIGURAÇÃO V2
TOTAL_CAPITAL_LIMIT = 30.0
MARGIN_PER_TRADE = 3.0
MAX_POSITIONS = 10
LEVERAGE = 50

# Lista de Ativos "High Volatility" que merecem Taker
# Baseado na lista recente: HYPE, LIT, SUI, DOGE parecem voláteis
HIGH_VOL_THRESHOLD = 0.02 # 2% change

def get_market_opportunities(transport):
    print("    Escaneando Mercado (V2 Logic)...")
    try:
        tickers = transport._send_request("GET", "/api/v1/tickers", "tickerQuery")
        if not tickers: return []
        
        perps = [t for t in tickers if 'PERP' in t['symbol'] and 'USDC' in t['symbol']]
        
        # Sort by Quote Volume
        sorted_perps = sorted(perps, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        
        opportunities = []
        for t in sorted_perps[:MAX_POSITIONS + 5]:
            symbol = t['symbol']
            price = float(t['lastPrice'])
            change_24h = float(t.get('priceChangePercent', 0))
            
            # Determine Strategy
            # Se volatilidade alta (>2% ou <-2%), usar Taker (Hyper Scalp)
            # Se volatilidade baixa, usar Maker (Sniper)
            
            strategy = "MAKER"
            if abs(change_24h) > HIGH_VOL_THRESHOLD:
                strategy = "TAKER"
            
            # HYPE exception: Always Taker due to extreme moves
            if "HYPE" in symbol or "LIT" in symbol:
                strategy = "TAKER"
                
            # Direction
            direction = "Buy" if change_24h > 0 else "Sell"
            
            opportunities.append({
                "symbol": symbol,
                "direction": direction,
                "strategy": strategy,
                "change": change_24h
            })
            
        return opportunities
    except Exception as e:
        print(f"    Erro ao buscar tickers: {e}")
        return []

def execute_strategy(opp):
    symbol = opp['symbol']
    side = opp['direction']
    strategy = opp['strategy']
    
    print(f"    DISPARANDO {symbol} [{side}] via {strategy}...")
    
    try:
        if strategy == "TAKER":
            # Usar hyper_scalp_50x.py diretamente (Fast)
            hyper_scalp_50x.hyper_scalp_execute(symbol, side)
            
        else:
            # Usar maker_sniper_50x.py diretamente (Fast)
            maker_sniper_50x.maker_sniper(symbol, side)
            
    except Exception as e:
        print(f"    Erro ao executar estratégia para {symbol}: {e}")

def omni_deploy_v2():
    print(" INICIANDO OMNI-DEPLOY V2 (HÍBRIDO MAKER/TAKER)")
    print(f" Capital Limite: ${TOTAL_CAPITAL_LIMIT} | Leverage: {LEVERAGE}x")
    
    transport = BackpackTransport()
    
    # 1. Check Balance
    balances = transport._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
    avail = float(balances.get('netEquityAvailable', 0)) if balances else 0
    print(f"    Saldo Disponível: ${avail:.2f}")
    
    if avail < MARGIN_PER_TRADE:
        print("    Saldo insuficiente.")
        return

    # 2. Get Opps
    opps = get_market_opportunities(transport)
    
    active_count = 0
    threads = []
    
    for opp in opps:
        if active_count >= MAX_POSITIONS: break
        if avail < (active_count + 1) * MARGIN_PER_TRADE: break
        
        print(f"    {opp['symbol']}: Vol {opp['change']*100:.2f}% -> {opp['strategy']} {opp['direction']}")
        
        t = threading.Thread(target=execute_strategy, args=(opp,))
        t.start()
        threads.append(t)
        
        active_count += 1
        time.sleep(1) # Rate limit safety
        
    print(f"\n {active_count} Estratégias Disparadas.")
    for t in threads:
        t.join()

if __name__ == "__main__":
    omni_deploy_v2()
