import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport
from core.book_scanner import BookScanner

def analyze_targets():
    print(" TARGET SCOPE: Analyzing Liquidity Walls (Exit Points)...")
    transport = BackpackTransport()
    
    targets = ["ETH_USDC_PERP", "SUI_USDC_PERP"]
    
    for symbol in targets:
        print(f"\n Analyzing {symbol}...")
        depth = transport.get_orderbook_depth(symbol)
        
        if not depth:
            print("    Failed to get depth.")
            continue
            
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # Como estamos SHORT, nosso alvo de saída é compra (Bids) lá embaixo.
        # Procuramos "Paredes" de liquidez nos Bids que podem segurar o preço.
        
        current_price = float(asks[0][0]) if asks else 0
        print(f"    Current Price: {current_price}")
        
        print("    Liquidity Walls (Support/Target):")
        
        max_bid_vol = 0
        wall_price = 0
        
        # Analisar Top 100 levels para ter profundidade real
        # A API pública retorna quantos? O default no transport é limit=5?
        # Precisamos pedir mais profundidade se possível, ou confiar no que vem.
        # Transport method 'get_orderbook_depth' usa limit no endpoint?
        # O código do transport usa apenas symbol na query, o que retorna depth default (geralmente 100).
        
        for price, qty in bids: # Scan all returned bids
            p = float(price)
            q = float(qty)
            vol = p * q
            
            # Filtrar preços muito distantes (Flash Crash Bids) que distorcem o alvo
            # Aceitar apenas paredes dentro de 10% do preço atual
            if p < current_price * 0.90:
                continue
            
            if vol > max_bid_vol:
                max_bid_vol = vol
                wall_price = p
                
            if vol > 10000: # Filtro menor para ver micro-suportes
                 print(f"      -> Support Wall @ {p} (Vol: ${vol:,.0f})")

        if wall_price > 0:
            dist = ((current_price - wall_price) / current_price) * 100
            print(f"    MAJOR REALISTIC TARGET (Biggest Wall < 10%): {wall_price} (-{dist:.2f}%)")
        else:
            print("   ️ No major wall found nearby.")

if __name__ == "__main__":
    analyze_targets()
