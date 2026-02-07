
import os
import sys
import requests
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def close_all_positions():
    print(" FECHANDO TODAS AS POSIÇÕES (MARKET CLOSE)...")
    load_dotenv()
    transport = BackpackTransport()
    
    try:
        # 1. Get Positions
        positions = transport._send_request("GET", "/api/v1/position", "positionQuery")
        
        if not positions:
            print(" Nenhuma posição aberta para fechar.")
            return

        print(f"️  Encontradas {len(positions)} posições. Executando Market Close...")
        
        for p in positions:
            symbol = p.get('symbol')
            side = p.get('side') # "Long" or "Short"
            qty = p.get('quantity') # Absolute value usually? Or signed?
            # API returns signed netQuantity usually, but let's check 'side'
            # If Side is Short, we Buy. If Long, we Sell.
            
            # Backpack Execute Order expects "Bid" (Buy) or "Ask" (Sell)
            close_side = "Bid" if side == "Short" else "Ask"
            
            # Quantity must be absolute string
            qty_abs = str(abs(float(qty)))
            
            print(f"    Fechando {symbol} ({side}) -> Executando {close_side} {qty_abs} a Mercado...")
            
            payload = {
                "symbol": symbol,
                "side": close_side,
                "orderType": "Market",
                "quantity": qty_abs
            }
            
            # Execute
            res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            print(f"      Resultado: {res}")
            
        print(" Todas as posições foram encerradas.")

    except Exception as e:
        print(f" Erro ao fechar posições: {e}")

if __name__ == "__main__":
    close_all_positions()
