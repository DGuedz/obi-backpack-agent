import sys
import os
import time
import requests
import json
import threading

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.backpack_transport import BackpackTransport
from tools.maker_sniper_50x import maker_sniper  # Reusing logic

# CONFIGURAÇÃO GERAL
TOTAL_CAPITAL_LIMIT = 30.0  # Usar até $30 do saldo total (Deixar $5 de reserva)
MARGIN_PER_TRADE = 3.0      # $3 por trade
MAX_POSITIONS = int(TOTAL_CAPITAL_LIMIT / MARGIN_PER_TRADE) # ~10 posições
LEVERAGE = 50

def get_top_assets(transport, limit=20):
    """Busca os Top Ativos por Volume 24h"""
    print("    Escaneando Mercado (Top Volume)...")
    try:
        tickers = transport._send_request("GET", "/api/v1/tickers", "tickerQuery")
        if not tickers: return []
        
        # Filtrar apenas PERP e USDC
        perps = [t for t in tickers if 'PERP' in t['symbol'] and 'USDC' in t['symbol']]
        
        # Sort by Quote Volume (liquidity proxy)
        # Ticker format: {'symbol': '...', 'quoteVolume': '...', ...}
        sorted_perps = sorted(perps, key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        
        return sorted_perps[:limit]
    except Exception as e:
        print(f"    Erro ao buscar tickers: {e}")
        return []

def analyze_direction(asset_ticker):
    """
    Decide direção Simples:
    Se Preço > 24h Low + (Range * 0.5) -> Buy (Acima da metade do range diário)
    Se Preço < 24h Low + (Range * 0.5) -> Sell (Abaixo da metade do range diário)
    Ou usar Price Change %: Positive = Buy, Negative = Sell.
    Vamos usar Price Change % 24h para seguir a tendência macro do dia.
    """
    change_24h = float(asset_ticker.get('priceChangePercent', 0))
    if change_24h > 0:
        return "Buy"
    else:
        return "Sell"

def deploy_sniper(symbol, direction):
    """Wrapper para rodar o maker_sniper em thread isolada"""
    # Hack: maker_sniper usa variáveis globais SYMBOL, SIDE no módulo original? 
    # Precisamos adaptar maker_sniper para aceitar parâmetros ou setar globais antes.
    # A função maker_sniper aceita 'side' como argumento, mas 'SYMBOL' é global no arquivo.
    # Vamos chamar o script via subprocess para garantir isolamento limpo.
    
    print(f"    DISPARANDO SNIPER EM {symbol} [{direction}]...")
    os.system(f"python3 tools/maker_sniper_50x_wrapper.py {symbol} {direction}")

def omni_deploy():
    print(" INICIANDO OMNI-DEPLOYER (MAKER SNIPER 50x) EM TODO O MERCADO")
    print(f" Capital Limite: ${TOTAL_CAPITAL_LIMIT} | Posições Máx: {MAX_POSITIONS}")
    
    transport = BackpackTransport()
    
    # 1. Checar Saldo Real
    balances = transport._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
    available_equity = 0.0
    if balances and 'netEquityAvailable' in balances:
        available_equity = float(balances['netEquityAvailable'])
    
    print(f"    Saldo Disponível: ${available_equity:.2f}")
    
    if available_equity < MARGIN_PER_TRADE:
        print("    Saldo insuficiente para iniciar.")
        return

    # 2. Selecionar Ativos
    top_assets = get_top_assets(transport, limit=MAX_POSITIONS + 5) # Pegar um pouco mais
    
    active_count = 0
    threads = []
    
    for asset in top_assets:
        if active_count >= MAX_POSITIONS:
            print("    Limite de Posições atingido.")
            break
            
        symbol = asset['symbol']
        
        # Check current price > 0
        if float(asset['lastPrice']) <= 0: continue
        
        direction = analyze_direction(asset)
        print(f"    Alvo: {symbol} | Change 24h: {asset.get('priceChangePercent')}% -> {direction}")
        
        # Disparar (Thread ou Subprocess)
        # Usando Threading para não bloquear, mas subprocess é mais seguro para scripts independentes.
        # Vamos usar subprocess em loop rápido.
        
        t = threading.Thread(target=deploy_sniper, args=(symbol, direction))
        t.start()
        threads.append(t)
        
        active_count += 1
        time.sleep(1) # Delay para não estourar Rate Limit de API na criação
        
    print(f"\n {active_count} Snipers Disparados. Monitorando logs individuais...")
    
    # Wait for threads (optional, or just exit and let them run in background?)
    # Se sair, as threads morrem? Sim. Precisamos de join.
    for t in threads:
        t.join()

if __name__ == "__main__":
    omni_deploy()
