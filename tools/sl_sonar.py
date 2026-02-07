
import asyncio
import logging
import sys
import os
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Add current directory to path to allow imports
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class SLSonar:
    """
     SL SONAR (Stop Loss Radar)
    Monitora continuamente posições abertas e verifica se existem ordens de Stop Loss associadas.
    Se detectar uma posição 'nua' (desprotegida), ativa o Escudo de Emergência.
    """
    def __init__(self, transport: BackpackTransport):
        self.transport = transport
        self.logger = logging.getLogger("SLSonar")
        self.EMERGENCY_SL_DIST = 0.05 # 5% de Distância para Stop de Emergência
        self.SCAN_INTERVAL = 5 # 5 segundos entre varreduras

    async def get_open_positions(self) -> List[Dict]:
        """Busca posições abertas com quantidade != 0"""
        try:
            positions = self.transport.get_positions()
            active_positions = [p for p in positions if float(p.get('quantity', 0)) != 0]
            return active_positions
        except Exception as e:
            self.logger.error(f"Erro ao buscar posições: {e}")
            return []

    async def get_active_orders(self, symbol: str) -> List[Dict]:
        """Busca ordens abertas para um símbolo específico"""
        try:
            # Nota: BackpackTransport.get_open_orders pode precisar de symbol ou retornar todas
            # Vamos assumir que retorna todas se symbol for None ou filtrar
            orders = self.transport.get_open_orders(symbol)
            return orders
        except Exception as e:
            self.logger.error(f"Erro ao buscar ordens para {symbol}: {e}")
            return []

    def is_protected(self, position: Dict, orders: List[Dict]) -> tuple[bool, bool]:
        """
        Verifica se a posição está protegida por Stop Loss (SL) e Take Profit (TP).
        Returns: (has_sl, has_tp)
        """
        raw_qty = float(position.get('netQuantity', position.get('quantity', 0)))
        pos_side = "Long" if raw_qty > 0 else "Short"
        required_order_side = "Ask" if pos_side == "Long" else "Bid"
        
        has_sl = False
        has_tp = False
        entry_price = float(position.get('entryPrice', 0))
        
        for order in orders:
            # Verifica Lado
            if order['side'] != required_order_side:
                continue
            
            order_type = order.get('orderType', '')
            price = float(order.get('price', 0)) if order.get('price') else 0
            trigger_price = float(order.get('triggerPrice', 0)) if order.get('triggerPrice') else 0
            
            # Check SL (Trigger Order)
            if ("Stop" in order_type) or (order_type == "Market" and trigger_price > 0):
                has_sl = True
                
            # Check TP (Limit Order no Lucro)
            if order_type == "Limit" and price > 0:
                if pos_side == "Long" and price > entry_price:
                    has_tp = True
                elif pos_side == "Short" and price < entry_price:
                    has_tp = True
                
        return has_sl, has_tp

    async def deploy_emergency_shield(self, position: Dict, missing_sl: bool, missing_tp: bool):
        """
        ️ ESCUDO DUPLO (SL + TP)
        Aplica ordens faltantes imediatamente.
        """
        symbol = position['symbol']
        raw_qty = float(position.get('netQuantity', position.get('quantity', 0)))
        qty = abs(raw_qty)
        entry_price = float(position['entryPrice'])
        side = "Long" if raw_qty > 0 else "Short"
        
        # Import Guardian for Precision
        from core.precision_guardian import PrecisionGuardian
        guardian = PrecisionGuardian(self.transport)
        
        qty_fmt = guardian.format_quantity(symbol, qty)
        
        # 1. STOP LOSS (Market Trigger)
        if missing_sl:
            self.logger.warning(f"️ {symbol}: SL Ausente! Ativando Escudo...")
            if side == "Long":
                sl_price = entry_price * (1 - self.EMERGENCY_SL_DIST)
                sl_side = "Ask"
            else:
                sl_price = entry_price * (1 + self.EMERGENCY_SL_DIST)
                sl_side = "Bid"
            
            sl_price_fmt = guardian.format_price(symbol, sl_price)
            
            payload_sl = {
                "symbol": symbol,
                "side": sl_side,
                "orderType": "Market",
                "quantity": qty_fmt,
                "triggerPrice": sl_price_fmt,
                "triggerQuantity": qty_fmt
            }
            res_sl = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload_sl)
            if res_sl: self.logger.info(f"    SL Cravado em {sl_price_fmt}")

        # 2. TAKE PROFIT (Limit Maker)
        if missing_tp:
            self.logger.warning(f" {symbol}: TP Ausente! Posicionando Alvo RR 1:4...")
            target_roe = self.TARGET_ROE
            
            if side == "Long":
                tp_price = entry_price * (1 + target_roe)
                tp_side = "Ask"
            else:
                tp_price = entry_price * (1 - target_roe)
                tp_side = "Bid"
                
            tp_price_fmt = guardian.format_price(symbol, tp_price)
            
            payload_tp = {
                "symbol": symbol,
                "side": tp_side,
                "orderType": "Limit",
                "quantity": qty_fmt,
                "price": tp_price_fmt,
                "postOnly": True
            }
            res_tp = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload_tp)
            if res_tp: self.logger.info(f"    TP Posicionado em {tp_price_fmt}")

    async def run(self):
        self.logger.info(" SL SONAR INICIADO - O RADAR DE SEGURANÇA")
        self.logger.info(f" Intervalo de Varredura: {self.SCAN_INTERVAL}s")
        self.logger.info(f"️ Distância de Emergência: {self.EMERGENCY_SL_DIST*100}%")
        
        while True:
            try:
                positions = await self.get_open_positions()
                
                if not positions:
                    # self.logger.info(" Nenhuma posição aberta. Radar em standby.")
                    pass
                else:
                    self.logger.info(f" Varrendo {len(positions)} posições ativas...")
                    
                    for pos in positions:
                        symbol = pos['symbol']
                        orders = await self.get_active_orders(symbol)
                        
                        has_sl, has_tp = self.is_protected(pos, orders)
                        
                        if has_sl and has_tp:
                            # self.logger.info(f" {symbol}: BLINDADO (SL+TP)")
                            pass
                        else:
                            await self.deploy_emergency_shield(pos, not has_sl, not has_tp)
                            
                await asyncio.sleep(self.SCAN_INTERVAL)
                
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    load_dotenv()
    transport = BackpackTransport()
    sonar = SLSonar(transport)
    
    try:
        asyncio.run(sonar.run())
    except KeyboardInterrupt:
        print("\n SL Sonar Desligado.")
