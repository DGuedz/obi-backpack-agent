from backpack_data import BackpackData

class LiquidityScout:
    """
    Agente de Liquidez e Book (The Scout)
    Missão: Analisar a profundidade do mercado e identificar "muros" para o Smart Exit.
    Contexto: Varre o Order Book para encontrar onde as baleias estão posicionadas.
    """
    def __init__(self, data_client: BackpackData):
        self.data = data_client

    def find_liquidity_walls(self, symbol, current_price, side="ask", scan_range_pct=0.05):
        """
        Identifies the largest liquidity wall within a % range of current price.
        Returns suggested Smart Exit price (front-running the wall).
        """
        print(f" Scout: Scanning {symbol} Liquidity Depth ({side.upper()})...")
        depth = self.data.get_order_book(symbol)
        
        if not depth:
            print("   ️ Scout: Blind (No Depth Data returned)")
            return None

        # Determine which side of book to scan
        # If we are Long, we want to sell into Asks -> Scan Asks for resistance
        # If we are Short, we want to buy from Bids -> Scan Bids for support
        book_side = 'asks' if side == 'ask' else 'bids'
        orders = depth.get(book_side, [])
        
        if not orders:
            return None
            
        # Define price limit for scanning
        limit_price = current_price * (1 + scan_range_pct) if side == 'ask' else current_price * (1 - scan_range_pct)
        
        max_wall_qty = 0
        wall_price = 0
        cumulative_vol = 0
        
        # Iterate through orders
        # API returns [[price, qty], [price, qty], ...]
        # Asks are usually sorted low->high. Bids high->low.
        for entry in orders:
            price = float(entry[0])
            qty = float(entry[1])
            
            # Check range
            if side == 'ask' and price > limit_price:
                break
            if side == 'bid' and price < limit_price:
                break
                
            cumulative_vol += qty
            
            # Identify "Wall" (Significant single price point liquidity)
            # Simple logic: Tracking the max single order level. 
            # Advanced: Could look for cluster.
            if qty > max_wall_qty:
                max_wall_qty = qty
                wall_price = price
                
        if wall_price == 0:
            print("   ️ Scout: No significant walls found in range.")
            return None

        # Calculate Smart Exit (Front-Run by 0.1%)
        smart_exit = 0
        if side == 'ask':
            smart_exit = wall_price * 0.999 # Sell just below resistance
        else:
            smart_exit = wall_price * 1.001 # Buy just above support
            
        print(f"    Scout: Wall Found at {wall_price} (Qty: {max_wall_qty:.2f})")
        print(f"    Scout: Smart Exit Suggested at {smart_exit:.4f}")
        
        return {
            "wall_price": wall_price,
            "wall_qty": max_wall_qty,
            "smart_exit_price": smart_exit,
            "cumulative_depth": cumulative_vol
        }
