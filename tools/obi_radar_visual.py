import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData

class OBIRadar:
    """
     OBI RADAR (Visualizador de Mercado)
    Monitora o Order Book Imbalance em tempo real para múltiplos ativos.
    Não executa trades, apenas exibe oportunidades.
    """
    def __init__(self):
        load_dotenv()
        if not os.getenv('BACKPACK_API_KEY'):
            print(" ERRO: Chaves de API não configuradas.")
            sys.exit(1)
            
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
        # Alvos para monitorar
        self.targets = ["SOL_USDC_PERP", "BTC_USDC_PERP", "SUI_USDC_PERP", "DOGE_USDC_PERP"]
        self.running = True

    def calculate_obi(self, depth):
        if not depth or 'bids' not in depth or 'asks' not in depth:
            return 0.0
            
        # Top 10 levels
        bids = depth['bids'][-10:] if len(depth['bids']) >= 10 else depth['bids']
        asks = depth['asks'][:10] if len(depth['asks']) >= 10 else depth['asks']
        
        bid_vol = sum([float(x[1]) for x in bids])
        ask_vol = sum([float(x[1]) for x in asks])
        total = bid_vol + ask_vol
        
        if total == 0: return 0.0
        
        return (bid_vol - ask_vol) / total

    async def scan_loop(self):
        print("\n OBI RADAR ACTIVATED - SCANNING MARKET FLOW...")
        print(f"   Targets: {', '.join(self.targets)}")
        print("   (Pressione Ctrl+C para parar)\n")
        
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI SCORE':<10} | {'STATUS':<15}")
        print("-" * 60)
        
        try:
            while self.running:
                # Move cursor up to overwrite previous lines (simple animation effect)
                # sys.stdout.write(f"\033[{len(self.targets)+1}A") 
                
                output_lines = []
                
                for symbol in self.targets:
                    # Synchronous call in async loop (ok for simple radar)
                    depth = self.data.get_orderbook_depth(symbol)
                    obi = self.calculate_obi(depth)
                    
                    # Price
                    best_bid = float(depth['bids'][-1][0]) if depth and depth.get('bids') else 0
                    best_ask = float(depth['asks'][0][0]) if depth and depth.get('asks') else 0
                    mid_price = (best_bid + best_ask) / 2
                    
                    # Status
                    status = "NEUTRAL"
                    color = "\033[0m" # Reset
                    
                    if obi > 0.35:
                        status = " BUY PRESSURE"
                        color = "\033[92m" # Green
                    elif obi > 0.85:
                        status = " MICRO SNIPER"
                        color = "\033[92;1m" # Bright Green
                    elif obi < -0.35:
                        status = " SELL PRESSURE"
                        color = "\033[91m" # Red
                    elif obi < -0.85:
                        status = " MICRO SNIPER"
                        color = "\033[91;1m" # Bright Red
                        
                    # Format Line
                    # symbol_fmt = f"{color}{symbol:<15}\033[0m"
                    # obi_fmt = f"{color}{obi:+.2f}{' '*(8-len(f'{obi:+.2f}'))}\033[0m"
                    
                    print(f"{color}{symbol:<15} | {mid_price:<10.4f} | {obi:+.4f}     | {status:<15}\033[0m")
                
                print("-" * 60)
                print(f"Last Update: {time.strftime('%H:%M:%S')}")
                
                # Small delay
                await asyncio.sleep(1)
                # Clear lines for next update (simple clear screen for better UX)
                print("\033c", end="") # Clear screen
                print("\n OBI RADAR ACTIVATED - SCANNING MARKET FLOW...")
                print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI SCORE':<10} | {'STATUS':<15}")
                print("-" * 60)

        except KeyboardInterrupt:
            print("\n RADAR STOPPED")

if __name__ == "__main__":
    radar = OBIRadar()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(radar.scan_loop())
    except KeyboardInterrupt:
        pass
