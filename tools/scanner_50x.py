import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

async def scan_50x_opportunities():
    print(f"\n SCANNER DE ALTA ALAVANCAGEM (50x) - MICRO SIZES ($3.00)")
    print(f"   Critério: Spread < 0.05% | OBI Forte | Liquidez Alta")
    print("-" * 100)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    print(" Baixando dados de mercado...")
    tickers = data_client.get_tickers()
    if not tickers:
        print(" Erro ao buscar tickers.")
        return []

    perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
    # Filtra por volume para garantir liquidez em 50x
    perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
    
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI':<6} | {'SPREAD %':<8} | {'SETUP 50x'}")
    print("-" * 100)
    
    opportunities = []
    
    for t in perps:
        try:
            symbol = t['symbol']
            price = float(t.get('lastPrice', 0))
            if price == 0: continue
            
            # 1. DEPTH & OBI
            depth = data_client.get_orderbook_depth(symbol)
            if not depth: continue
            
            obi = oracle.calculate_obi(depth)
            
            # 2. SPREAD CHECK RIGOROSO (50x requer spread mínimo)
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            spread_pct = ((best_ask - best_bid) / best_bid) * 100
            
            # Filtro 50x: Spread deve ser menor que 0.06% para não ser engolido na entrada
            if spread_pct > 0.06: continue
            
            # 3. FILTRO DE FLUXO (OBI)
            setup = "-"
            if obi > 0.20:
                setup = "🟢 LONG"
                opportunities.append(symbol)
            elif obi < -0.20:
                setup = " SHORT"
                opportunities.append(symbol)
            
            if setup != "-":
                print(f"{symbol:<15} | {price:<10.4f} | {obi:<6.2f} | {spread_pct:>7.4f}% | {setup}")
                
            if len(opportunities) >= 10: break # Pega os Top 10 melhores
        
        except Exception:
            continue
            
    print("-" * 100)
    return opportunities

if __name__ == "__main__":
    opps = asyncio.run(scan_50x_opportunities())
    if opps:
        symbols_str = " ".join(opps)
        print(f"\n ATIVOS SELECIONADOS: {symbols_str}")
        print("\n COMANDO PARA EXECUTAR 100 OPERAÇÕES:")
        print(f"python3 tools/volume_farmer.py --turbo --leverage 50 --size 3.0 --symbols {symbols_str}")
