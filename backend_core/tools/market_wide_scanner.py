import asyncio
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

async def scan_market_wide():
    print(f"\n MARKET WIDE SCANNER (Opportunity Hunter)")
    print(f"   Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 100)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    # 1. Buscar todos os tickers para filtrar por volume
    print(" Baixando dados de mercado...")
    tickers = data_client.get_tickers()
    if not tickers:
        print(" Erro ao buscar tickers.")
        return

    perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
    perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
    
    # SCANNER AMPLIADO PARA TODOS OS ATIVOS DISPONÍVEIS (VARREDURA TOTAL)
    top_perps = perps # Sem corte, analisa TUDO
    
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI':<6} | {'SPREAD %':<8} | {'SETUP'}")
    print("-" * 100)
    
    opportunities = []
    
    for t in top_perps:
        try:
            symbol = t['symbol']
            price = float(t.get('lastPrice', 0))
            if price == 0: continue
            
            # 1. DEPTH & OBI
            depth = data_client.get_orderbook_depth(symbol)
            if not depth: continue
            
            obi = oracle.calculate_obi(depth)
            
            # 2. SPREAD CHECK (Custo da Operação)
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            
            # 3. FILTRO DE QUALIDADE (SETUP MICRO SCALP LOOP)
            # - Spread Baixo (< 0.08% idealmente, max 0.15%)
            # - OBI Forte (> 0.25 ou < -0.25)
            # - Preço "Barato" (Opcional, mas ajuda no psicológico)
            
            setup = "-"
            
            if spread_pct < 0.15: # Spread Aceitável
                if obi > 0.25:
                    setup = "🟢 LONG SCALP"
                    opportunities.append({'symbol': symbol, 'side': 'Long', 'obi': obi, 'spread': spread_pct})
                elif obi < -0.25:
                    setup = " SHORT SCALP"
                    opportunities.append({'symbol': symbol, 'side': 'Short', 'obi': obi, 'spread': spread_pct})
            
            if setup != "-":
                print(f"{symbol:<15} | {price:<10.4f} | {obi:<6.2f} | {spread_pct:>7.4f}% | {setup}")
        
        except Exception as e:
            continue
            
    print("-" * 100)
    print(f" OPORTUNIDADES FILTRADAS: {len(opportunities)}")
    
    # GERAR COMANDO SUGERIDO
    if opportunities:
        symbols_str = " ".join([o['symbol'] for o in opportunities[:10]]) # Top 10 para não sobrecarregar
        print("\n COMANDO SUGERIDO (COPIE E RODE):")
        print(f"python3 tools/volume_farmer.py --turbo --leverage 5 --size 12.0 --symbols {symbols_str}")

    return opportunities

if __name__ == "__main__":
    asyncio.run(scan_market_wide())
