import os
import sys
import asyncio
import logging
import argparse
import time
from dotenv import load_dotenv

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("passive_grid.log"),
        logging.StreamHandler()
    ]
)

class PassiveGridBot:
    def __init__(self, symbol, quantity, grid_lines=4, grid_spread=0.005):
        load_dotenv()
        self.symbol = symbol
        self.quantity = quantity # Qtd por ordem
        self.grid_lines = grid_lines # Linhas por lado (Bid/Ask)
        self.grid_spread = grid_spread # 0.5% de distância entre linhas
        
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        self.logger = logging.getLogger(f"Grid-{symbol}")
        
        self.is_running = False
        self.active_orders = []

    async def start(self):
        self.logger.info(f"️ INICIANDO PASSIVE GRID: {self.symbol}")
        self.logger.info(f"   -> Qtd: {self.quantity} | Lines: {self.grid_lines} | Spread: {self.grid_spread*100}%")
        
        self.is_running = True
        
        # Initial Grid Placement
        await self._refresh_grid()
        
        while self.is_running:
            try:
                await self._monitor_grid()
                await asyncio.sleep(10) # Verifica a cada 10s
            except Exception as e:
                self.logger.error(f"Erro no loop: {e}")
                await asyncio.sleep(5)

    async def _refresh_grid(self):
        """Cancela tudo e reposiciona o Grid em torno do preço atual"""
        self.logger.info("️ Recalibrando Grid...")
        
        # 1. Cancel All
        open_orders = self.transport.get_open_orders(self.symbol)
        for o in open_orders:
             self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': self.symbol, 'orderId': o['id']})
        
        # 2. Get Price
        ticker = self.transport.get_ticker(self.symbol)
        if not ticker: return
        mid_price = float(ticker['lastPrice'])
        
        # 3. Place Bids (Abaixo)
        for i in range(1, self.grid_lines + 1):
            price = mid_price * (1 - (self.grid_spread * i))
            price = self._round_price(price)
            await self._place_order("Buy", price)
            
        # 4. Place Asks (Acima)
        for i in range(1, self.grid_lines + 1):
            price = mid_price * (1 + (self.grid_spread * i))
            price = self._round_price(price)
            await self._place_order("Sell", price)
            
        self.logger.info(f" Grid Posicionado em torno de ${mid_price}")

    async def _place_order(self, side, price):
        api_side = "Bid" if side == "Buy" else "Ask"
        payload = {
            "symbol": self.symbol,
            "side": api_side,
            "orderType": "Limit",
            "quantity": str(self.quantity),
            "price": str(price),
            "postOnly": True
        }
        res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        if res and 'id' in res:
            self.logger.info(f" {side} Limit @ {price}")

    async def _monitor_grid(self):
        """Verifica se alguma ordem foi executada e repõe o lado oposto (Ping-Pong)"""
        # Se posição ficar muito grande, ou preço sair do range, recalibrar?
        # Por enquanto, simples: Se ordem sumiu e não foi cancelada, foi Fill.
        # Mas a API não avisa fácil.
        # Melhor estratégia simples: Se ordens abertas < (grid_lines * 2), algo aconteceu.
        
        open_orders = self.transport.get_open_orders(self.symbol)
        if len(open_orders) < (self.grid_lines * 2):
            self.logger.info(" Ordem Executada! Detectando mudança...")
            
            # Verifica Posição
            positions = self.transport.get_positions()
            my_pos = next((p for p in positions if p['symbol'] == self.symbol), None)
            
            if my_pos:
                qty = float(my_pos['netQuantity'])
                self.logger.info(f" Posição Atual: {qty} {self.symbol}")
                
                # Se acumulou muito (Tendência forte contra), talvez stopar?
                # Grid assume lateralidade. Se tendência, Grid perde.
                # Proteção básica: Se PnL < -5%, Emergency Close.
                
            # Simplesmente repõe o grid inteiro centrado no novo preço?
            # Isso é 'Trailing Grid'.
            await self._refresh_grid()

    def _round_price(self, price):
        if "BTC" in self.symbol: return round(price, 1)
        if "ETH" in self.symbol: return round(price, 2)
        if "SOL" in self.symbol: return round(price, 2)
        return round(price, 4)

if __name__ == "__main__":
    # Ex: python3 passive_grid.py --symbol SOL_USDC_PERP --qty 1.0
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='SOL_USDC_PERP')
    parser.add_argument('--qty', type=float, default=1.0)
    args = parser.parse_args()
    
    bot = PassiveGridBot(args.symbol, args.qty)
    asyncio.run(bot.start())
