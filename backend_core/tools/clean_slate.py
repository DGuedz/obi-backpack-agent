import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

async def clean_slate():
    load_dotenv()
    transport = BackpackTransport()
    
    symbols = ["SOL_USDC_PERP", "SUI_USDC_PERP", "SEI_USDC_PERP", "ETH_USDC_PERP", "DOGE_USDC_PERP", "AVAX_USDC_PERP", "APT_USDC_PERP"]
    
    print(" LIMPANDO ORDENS PENDENTES (FARMER SYMBOLS)...")
    
    for symbol in symbols:
        try:
            print(f"   -> Cancelando {symbol}...")
            transport._send_request("DELETE", "/api/v1/orders", "orderCancelAll", {'symbol': symbol})
        except Exception as e:
            print(f"      Erro em {symbol}: {e}")
            
    print(" LIMPEZA CONCLUÍDA.")

if __name__ == "__main__":
    asyncio.run(clean_slate())
