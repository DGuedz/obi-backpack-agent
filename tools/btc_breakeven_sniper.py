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

async def sniper_btc_breakeven():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    transport = BackpackTransport()
    
    symbol = "BTC_USDC_PERP"
    
    # Meta: "Se Pagar"
    # Taxas estimadas (Entrada + Saída): ~0.12% do Notional
    # Se posição é $400, taxa é ~$0.50.
    # Vamos colocar alvo de $0.60 para garantir que pagou e sobrou um café.
    target_profit_usd = 0.60  
    
    print(f"\n BTC BREAKEVEN SNIPER (Mode: 'Pagou Saiu')")
    print(f"   Alvo Mínimo: +${target_profit_usd} (Cobre Taxas + Spread)")
    
    try:
        while True:
            positions = transport.get_positions()
            btc_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not btc_pos:
                print("   ️ Posição BTC fechada. Missão cumprida ou stopada.")
                break
                
            pnl = float(btc_pos.get('pnlUnrealized', 0))
            side = "Long" if float(btc_pos.get('netQuantity', 0)) > 0 else "Short"
            qty = abs(float(btc_pos.get('netQuantity')))
            
            # Log de status (menos spam)
            print(f"   ⏳ BTC PnL: ${pnl:.2f}...", end="\r")
            
            if pnl >= target_profit_usd:
                print(f"\n    BTC SE PAGOU! Lucro: ${pnl:.2f}. SAINDO AGORA...")
                
                # Fechar a mercado
                trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    order_type="Market",
                    quantity=str(qty),
                    price=None
                )
                print("    BTC LIBERADO. CAPITAL RECUPERADO.")
                break
            
            await asyncio.sleep(0.5) 

    except Exception as e:
        print(f"\n ERRO: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sniper_btc_breakeven())
