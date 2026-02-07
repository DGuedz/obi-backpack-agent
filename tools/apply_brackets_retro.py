import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_transport import BackpackTransport

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("RetroBracket")

class RetroBracket:
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.transport = BackpackTransport() # Legacy transport for get_positions
        
    def run(self):
        logger.info("️ INICIANDO PROTEÇÃO RETROATIVA DE POSIÇÕES...")
        
        # 1. Get Positions
        positions = self.transport.get_positions()
        if not positions:
            logger.info(" Nenhuma posição aberta para proteger.")
            return

        for p in positions:
            symbol = p['symbol']
            side = p.get('side') # Long/Short (Position side)
            qty = float(p.get('netQuantity', p.get('quantity')))
            entry = float(p['entryPrice'])
            
            if qty == 0: continue
            
            logger.info(f" Protegendo {symbol} ({side}) | Entry: {entry}")
            
            # Configuração AWM (Recovery Mode)
            sl_pct = 0.015 # 1.5%
            tp_pct = 0.04  # 4.0%
            
            # Definir Preços e Lado da Ordem de Saída
            if side == "Long":
                sl_price = entry * (1 - sl_pct)
                tp_price = entry * (1 + tp_pct)
                exit_side = "Ask" # Sell to Close
            else: # Short
                sl_price = entry * (1 + sl_pct)
                tp_price = entry * (1 - tp_pct)
                exit_side = "Bid" # Buy to Close
                
            # Formatar preços com base no valor nominal (Tick Size Heurístico)
            decimals = 2 # Default
            
            if entry > 1000: 
                decimals = 1 # BTC, ETH
            elif entry > 10:
                decimals = 2 # SOL, BNB
            elif entry > 1:
                decimals = 3 # SUI, XRP
            elif entry > 0.01:
                decimals = 5 # DOGE, FOGO
            else:
                decimals = 6 # MEME
            
            sl_price = round(sl_price, decimals)
            tp_price = round(tp_price, decimals)
            
            # Enviar Ordens (Usando execute_order corrigido)
            # Stop Loss
            logger.info(f"    Placing Stop Loss @ {sl_price}")
            self.trade.execute_order(
                symbol=symbol,
                side=exit_side,
                price="0", # Dummy
                quantity=abs(qty),
                order_type="StopLoss",
                trigger_price=str(sl_price)
            )
            
            # Take Profit
            logger.info(f"    Placing Take Profit @ {tp_price}")
            self.trade.execute_order(
                symbol=symbol,
                side=exit_side,
                price="0", # Dummy
                quantity=abs(qty),
                order_type="TakeProfit",
                trigger_price=str(tp_price)
            )

if __name__ == "__main__":
    bot = RetroBracket()
    bot.run()
