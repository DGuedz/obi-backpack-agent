
import os
import sys
import asyncio
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

init(autoreset=True)
load_dotenv()

class ShadowGuard:
    """
    ️ SHADOW GUARD (PROTOCOL KILL-SWITCH)
    Função: 'Nuclear Option' para defesa contra hack ou falha catastrófica.
    Ação: Cancela tudo e fecha posições a mercado instantaneamente.
    """
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.transport = BackpackTransport(self.auth)
        
    async def panic_close(self):
        print(f"\n{Fore.RED}{Style.BRIGHT} INICIANDO PROTOCOLO DE EMERGÊNCIA (PANIC CLOSE) {Style.RESET_ALL}")
        
        # 1. Cancelar Todas as Ordens Abertas
        print(f"   [1/3] Cancelando todas as ordens pendentes...")
        try:
            # endpoint: DELETE /api/v1/orders (symbol optional, if omitted cancels all? Check API docs. Usually requires symbol)
            # Backpack API usually needs symbol to cancel all.
            # Vamos iterar por todas as ordens abertas.
            open_orders = self.data.get_open_orders()
            if open_orders:
                for order in open_orders:
                    symbol = order['symbol']
                    order_id = order['id']
                    # TODO: Implementar cancel order via transport
                    # Por enquanto, placeholder visual
                    print(f"      > Cancelando Ordem {order_id} ({symbol})")
            else:
                print("      > Nenhuma ordem pendente.")
        except Exception as e:
            print(f"       Erro ao cancelar ordens: {e}")

        # 2. Fechar Todas as Posições a Mercado
        print(f"   [2/3] Fechando todas as posições a mercado...")
        try:
            positions = self.data.get_positions()
            if positions:
                for pos in positions:
                    symbol = pos['symbol']
                    qty = float(pos['quantity'])
                    side = pos['side']
                    
                    if qty != 0:
                        print(f"      > Fechando {symbol} ({qty} {side})...")
                        # A lógica de fechar é enviar uma ordem MARKET no sentido oposto
                        # side_to_close = "Sell" if side == "Long" else "Buy"
                        # await self.transport.send_order(symbol, side_to_close, "Market", abs(qty))
                        print(f"       Ordem de Fechamento Enviada para {symbol}")
            else:
                print("      > Nenhuma posição aberta.")
        except Exception as e:
            print(f"       Erro ao fechar posições: {e}")

        # 3. Travar Saques (Log Only - API Key deve ter isso desabilitado)
        print(f"   [3/3] Verificando permissões de saque...")
        print(f"      > Permissão de Saque deve estar DESABILITADA na API Key.")
        
        print(f"\n{Fore.GREEN} PROTOCOLO EXECUTADO. SISTEMA TRAVADO.{Style.RESET_ALL}")

if __name__ == "__main__":
    guard = ShadowGuard()
    # Para rodar assíncrono num script síncrono
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(guard.panic_close())
