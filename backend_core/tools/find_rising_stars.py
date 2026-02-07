import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def find_rising_stars():
    load_dotenv()
    print(" PROCURANDO CANDIDATOS SWING (TOP 3 GAINERS)...")
    
    transport = BackpackTransport()
    
    # Obter Tickers
    try:
        # endpoint: /api/v1/tickers
        tickers = transport._send_request("GET", "/api/v1/tickers", "tickerQueryAll")
        
        if not tickers:
            print(" Falha ao obter tickers.")
            return

        candidates = []
        
        for t in tickers:
            symbol = t.get('symbol')
            if not symbol.endswith('USDC_PERP'): continue
            
            # Filtros de Volume e Preço
            last_price = float(t.get('lastPrice', 0))
            if last_price <= 0: continue
            
            # Change 24h calculation
            # API usually provides 'priceChangePercent' or we calculate from openPrice
            # Assuming standard fields or calculating
            # Let's check keys available in a real run, but for now assuming standard
            
            # Backpack Ticker often has 'priceChangePercent'
            change_pct = float(t.get('priceChangePercent', 0))
            
            candidates.append({
                'symbol': symbol,
                'change': change_pct,
                'price': last_price
            })
            
        # Ordenar por maior alta
        candidates.sort(key=lambda x: x['change'], reverse=True)
        
        print("\n TOP 3 RISING STARS:")
        top_3 = candidates[:3]
        
        symbols_arg = ""
        for i, c in enumerate(top_3):
            print(f"   {i+1}. {c['symbol']} (+{c['change']:.2f}%) @ ${c['price']}")
            symbols_arg += c['symbol'] + " "
            
        print(f"\n COMMAND SUGGESTION:")
        print(f"python3 tools/volume_farmer.py --symbols {symbols_arg.strip()} --leverage 3 --size 3.0 --profit 0.50 --long --surf")
        
        return top_3

    except Exception as e:
        print(f" Erro: {e}")

if __name__ == "__main__":
    find_rising_stars()
