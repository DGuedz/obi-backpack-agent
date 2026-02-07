import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

async def execute_emergency_cut():
    print(" EMERGENCY CUT: Fechando posições perdedoras IMEDIATAMENTE!")
    load_dotenv()
    transport = BackpackTransport()
    
    positions = transport.get_positions()
    
    if not positions:
        print(" Nenhuma posição aberta para fechar.")
        return

    for p in positions:
        symbol = p.get('symbol')
        qty = float(p.get('netQuantity'))
        pnl = float(p.get('unrealizedPnl', 0))
        
        # Só fecha se estiver negativo (Loss > 0.05 ou Loss > 3%)
        if pnl < -0.05: 
            print(f" FECHANDO {symbol} (Loss: ${pnl:.2f})")
            
            side = "Short" if qty < 0 else "Long"
            exit_side = "Sell" if side == "Long" else "Buy"
            
            # Ordem a Mercado
            transport.execute_order(symbol, "Market", exit_side, abs(qty))
            
            # Cancela tudo desse símbolo
            transport._send_request("DELETE", "/api/v1/orders", "orderCancelAll", {'symbol': symbol})
            
    print(" CORTES EXECUTADOS. Carteira limpa de sangramento.")

if __name__ == "__main__":
    asyncio.run(execute_emergency_cut())
