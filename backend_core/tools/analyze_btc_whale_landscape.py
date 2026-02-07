
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def analyze_whale_landscape(symbol="BTC_USDC_PERP"):
    transport = BackpackTransport()
    print(f" OBI WHALE LANDSCAPE ANALYZER ({symbol})")
    print("   Scanning Order Book Depth for Liquidity Walls & Traps...\n")
    
    try:
        # 1. Fetch Deep Order Book
        depth = transport.get_orderbook_depth(symbol, limit=100) # Max depth usually allowed
        if not depth:
            print("    Error fetching depth.")
            return

        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # 2. Process Liquidity
        # Convert to list of (price, qty, notional)
        bid_levels = []
        for p, q in bids:
            price = float(p)
            qty = float(q)
            notional = price * qty
            bid_levels.append({'price': price, 'qty': qty, 'notional': notional})
            
        ask_levels = []
        for p, q in asks:
            price = float(p)
            qty = float(q)
            notional = price * qty
            ask_levels.append({'price': price, 'qty': qty, 'notional': notional})
            
        # 3. Identify "Walls" (Large Orders > $100k or relative size)
        # Calculate average order size to define "Whale"
        avg_bid_size = sum(b['notional'] for b in bid_levels) / len(bid_levels) if bid_levels else 0
        whale_threshold = max(50000, avg_bid_size * 3) # Dynamic threshold or $50k min
        
        print(f"    Whale Threshold: ${whale_threshold/1000:.1f}k")
        
        print("\n🟢 BID WALLS (Suporte/Compra):")
        bid_walls = [b for b in bid_levels if b['notional'] > whale_threshold]
        # Sort by Price Descending (Nearest to price first)
        bid_walls.sort(key=lambda x: x['price'], reverse=True)
        
        if not bid_walls:
            print("   (No major walls nearby)")
        for w in bid_walls[:5]: # Top 5
            print(f"    ${w['price']:.2f} | Size: {w['qty']:.3f} BTC | Val: ${w['notional']/1000:.1f}k")
            
        print("\n ASK WALLS (Resistência/Venda):")
        ask_walls = [a for a in ask_levels if a['notional'] > whale_threshold]
        # Sort by Price Ascending (Nearest to price first)
        ask_walls.sort(key=lambda x: x['price'])
        
        if not ask_walls:
            print("   (No major walls nearby)")
        for w in ask_walls[:5]: # Top 5
            print(f"    ${w['price']:.2f} | Size: {w['qty']:.3f} BTC | Val: ${w['notional']/1000:.1f}k")

        # 4. Calculate Liquidity Imbalance (The "Tilt")
        total_bid_liq = sum(b['notional'] for b in bid_levels)
        total_ask_liq = sum(a['notional'] for a in ask_levels)
        
        imbalance = (total_bid_liq - total_ask_liq) / (total_bid_liq + total_ask_liq) * 100
        
        print("\n️ LIQUIDITY IMBALANCE (Quem está segurando o jogo?):")
        print(f"   Total Bids (Compradores): ${total_bid_liq/1000000:.2f}M")
        print(f"   Total Asks (Vendedores):  ${total_ask_liq/1000000:.2f}M")
        
        if imbalance > 5:
            print(f"    BULLISH TILT (+{imbalance:.1f}%): Paredão de Compra segurando o preço.")
        elif imbalance < -5:
            print(f"    BEARISH TILT ({imbalance:.1f}%): Paredão de Venda bloqueando a subida.")
        else:
            print(f"   ️ NEUTRAL ({imbalance:.1f}%): Forças equilibradas (Consolidação).")
            
        # 5. The "Magnet" Theory
        # Price often gravitates towards the thickest liquidity to fill orders.
        # Find the single largest wall in the book
        all_walls = bid_walls + ask_walls
        if all_walls:
            biggest_wall = max(all_walls, key=lambda x: x['notional'])
            wall_type = "SUPPORT" if biggest_wall in bid_walls else "RESISTANCE"
            print(f"\n LIQUIDITY MAGNET (Onde o Market Maker quer ir?):")
            print(f"   O maior bloco de ordens está em ${biggest_wall['price']:.2f} ({wall_type}).")
            print(f"   Valor: ${biggest_wall['notional']/1000:.1f}k")
            print(f"   Cenário: O preço pode ser atraído para lá para buscar liquidez.")

    except Exception as e:
        print(f"    Analysis Error: {e}")

if __name__ == "__main__":
    analyze_whale_landscape()
