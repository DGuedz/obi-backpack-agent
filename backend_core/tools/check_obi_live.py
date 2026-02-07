import os
import sys
import asyncio
from tabulate import tabulate

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'obiwork_core'))

from obiwork_core.core.backpack_transport import BackpackTransport
from obiwork_core.core.backpack_data import BackpackData
from obiwork_core.core.backpack_auth import BackpackAuth
from obiwork_core.core.technical_oracle import TechnicalOracle
from dotenv import load_dotenv

load_dotenv()

async def main():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    symbols = ['BTC_USDC_PERP', 'SOL_USDC_PERP', 'ETH_USDC_PERP', 'SUI_USDC_PERP', 'DOGE_USDC_PERP']
    
    print("\n MONITOR DE OBI EM TEMPO REAL (OBI WATCH)")
    print("-" * 60)
    
    results = []
    
    for symbol in symbols:
        depth = data.get_depth(symbol)
        if not depth:
            results.append([symbol, "ERROR", "N/A"])
            continue
            
        obi = oracle.calculate_obi(depth)
        
        # Formatação Visual
        obi_str = f"{obi:.2f}"
        status = "NEUTRO"
        
        if obi > 0.6: status = "🟢 BUY (STRONG)"
        elif obi > 0.25: status = "🟢 BUY (WEAK)"
        elif obi < -0.6: status = " SELL (STRONG)"
        elif obi < -0.25: status = " SELL (WEAK)"
        
        results.append([symbol, obi_str, status])
        
    print(tabulate(results, headers=["Symbol", "OBI Score", "Signal (Threshold 0.6)"], tablefmt="grid"))
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
