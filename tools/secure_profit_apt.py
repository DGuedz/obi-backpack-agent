import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from core.backpack_transport import BackpackTransport

async def secure_fuel():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    transport = BackpackTransport()
    
    print("\n GERENCIADOR DE COMBUSTÍVEL (NO LOSS PROTOCOL)\n")
    
    try:
        # Get Positions
        positions = transport.get_positions()
        print(f"DEBUG: Positions Raw: {positions}")
        
        for p in positions:
            symbol = p['symbol']
            side = "Long" if float(p.get('netQuantity', 0)) > 0 else "Short"
            qty = abs(float(p['netQuantity'])) # Use absolute quantity
            pnl = float(p.get('pnlUnrealized', 0))
            
            if symbol == "APT_USDC_PERP" and side == "Short":
                # Check for positive PnL (even small) or just close because OBI is dangerous
                if pnl > 0 or True: # Force Close because OBI is Bullish against Short
                    print(f" APT SHORT: Encerrando posição.")
                    print("   ️ ALERTA: Fluxo de mercado virou ALTA (Bullish).")
                    print("    AÇÃO: Realizar Lucro/Proteção AGORA para garantir combustível.")
                    
                    # Manual close call
                    # Use 'Bid' for Buy (Closing Short), 'Ask' for Sell (Closing Long)
                    side_to_close = "Bid" 
                    
                    trade.execute_order(
                        symbol=symbol,
                        side=side_to_close, 
                        order_type="Market",
                        quantity=str(qty),
                        price=None
                    )
                    print("    SUCESSO: Ordem de saída enviada.")
                    
            elif symbol in ["BTC_USDC_PERP", "SOL_USDC_PERP"]:
                print(f"️ {symbol} {side}: PnL {pnl:.2f}. HOLDING FOR RECOVERY. (Fluxo a favor)")

    except Exception as e:
        print(f" ERRO: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(secure_fuel())
