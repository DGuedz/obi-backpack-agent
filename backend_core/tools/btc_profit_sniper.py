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

async def sniper_btc_profit():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    transport = BackpackTransport()
    
    symbol = "BTC_USDC_PERP"
    target_profit_usd = 0.50  # Lucro Mínimo Absoluto em Dólares para cobrir taxas + profit
    
    print(f"\n BTC PROFIT SNIPER ACTIVATED (Target: +${target_profit_usd})")
    
    try:
        while True:
            positions = transport.get_positions()
            btc_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if not btc_pos:
                print("   ️ Posição BTC não encontrada. Encerrando.")
                break
                
            pnl = float(btc_pos.get('pnlUnrealized', 0))
            side = "Long" if float(btc_pos.get('netQuantity', 0)) > 0 else "Short"
            qty = abs(float(btc_pos.get('netQuantity')))
            
            print(f"    BTC PnL: ${pnl:.2f} | Alvo: ${target_profit_usd}")
            
            if pnl >= target_profit_usd:
                print(f"    ALVO ATINGIDO! Lucro: ${pnl:.2f}. EXECUTANDO SAÍDA...")
                
                # Fechar a mercado
                trade.execute_order(
                    symbol=symbol,
                    side="Ask" if side == "Long" else "Bid",
                    order_type="Market",
                    quantity=str(qty),
                    price=None
                )
                print("    BTC ENCERRADO COM LUCRO GARANTIDO.")
                break
            
            await asyncio.sleep(1) # Monitoramento agressivo (1s)

    except Exception as e:
        print(f" ERRO: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sniper_btc_profit())
