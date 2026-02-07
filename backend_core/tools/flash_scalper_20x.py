import asyncio
import os
import sys
import logging
import time
import argparse
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from tools.vsc_transformer import VSCLayer
from tools.market_proxy_oracle import MarketProxyOracle
from tools.panic_sentinel import PanicSentinel
from tools.integrity_audit import IntegrityAudit
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from core.backpack_transport import BackpackTransport

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FlashScalper20x")

class FlashScalper20x:
    """
     FLASH SCALPER 20x (MANUAL EXIT MODE)
    Monitora continuamente múltiplos ativos, entra com 20x de alavancagem
    e deixa a saída de lucro (TP) para o operador manual (User).
    Apenas Stop Loss de emergência é configurado.
    """
    def __init__(self, symbols, margin_usd=20.0, leverage=20):
        self.symbols = symbols
        self.margin_usd = margin_usd
        self.leverage = leverage
        self.notional_usd = margin_usd * leverage
        
        # Load Env
        load_dotenv()
        if not os.getenv('BACKPACK_API_KEY'):
            raise ValueError("Chaves de API não configuradas.")
            
        # Initialize Stack
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.transport = BackpackTransport()
        
        self.vsc = VSCLayer()
        self.oracle = MarketProxyOracle(self.vsc)
        self.sentinel = PanicSentinel()
        self.audit = IntegrityAudit()
        
        self.is_running = False
        self.cooldowns = {s: 0 for s in symbols} # Cooldown timestamp per symbol
        self.active_positions = set()

    async def check_existing_positions(self):
        """Atualiza lista de posições ativas para evitar re-entrada"""
        try:
            # Note: get_positions is sync in legacy transport
            positions = self.transport.get_positions() 
            current_symbols = set()
            if positions:
                for p in positions:
                    if float(p.get('netQuantity', 0)) != 0:
                        current_symbols.add(p['symbol'])
            self.active_positions = current_symbols
            logger.info(f" Active Positions: {self.active_positions}")
        except Exception as e:
            logger.error(f"Error checking positions: {e}")

    async def set_safety_stop(self, symbol, quantity, entry_price, side):
        """Define APENAS Stop Loss de emergência (Sem TP)"""
        try:
            sl_pct = 0.015 # 1.5% Stop (30% PnL Loss at 20x) - TIGHT SAFETY
            
            if side == "Buy":
                sl_price = entry_price * (1 - sl_pct)
                exit_side = "Ask"
            else:
                sl_price = entry_price * (1 + sl_pct)
                exit_side = "Bid"
                
            sl_price = round(sl_price, 5) # 5 decimals safer for low price assets
            
            logger.info(f"️ SAFETY STOP: {symbol} SL @ {sl_price} (User Manual Exit for Profit)")
            
            # Stop Loss (Trigger Market)
            self.trade.execute_order(
                symbol=symbol,
                side=exit_side,
                price="0",
                quantity=quantity,
                order_type="StopLoss",
                trigger_price=str(sl_price)
            )
            
        except Exception as e:
            logger.error(f" STOP LOSS ERROR for {symbol}: {e}")

    async def execute_flash_entry(self, symbol, side, price):
        """Executa entrada rápida"""
        logger.warning(f" FLASH ENTRY: {side} {symbol} @ {price} | 20x LEVERAGE")
        
        # 1. Calculate Quantity
        # Reduce margin per trade slightly to fit more orders if margin is tight?
        # Or keep aggressive. User said "abrir mais ordens".
        # Let's try to dynamically adjust size if margin is low?
        # For now, keep fixed $20 margin but handle error gracefully.
        
        raw_qty = self.notional_usd / price
        
        # 2. Spec Check (Step Size)
        spec = await self.sentinel._get_asset_spec_vsc(symbol)
        step_size = float(spec.split('|')[2]) if spec else 1.0
        
        import math
        final_qty = math.floor(raw_qty / step_size) * step_size
        
        # Format decimal places
        import decimal
        d = decimal.Decimal(str(step_size))
        decimals = abs(d.as_tuple().exponent)
        fmt_qty = f"{final_qty:.{decimals}f}"

        order_payload = {
            "symbol": symbol,
            "side": "Bid" if side == "Buy" else "Ask",
            "orderType": "Market",
            "quantity": fmt_qty
        }
        
        # 3. Execute
        result = self.trade.execute_order(
            symbol=order_payload["symbol"],
            side=order_payload["side"],
            order_type=order_payload["orderType"],
            quantity=order_payload["quantity"],
            price=None
        )
        
        # Check for Insufficient Margin in result (if result is dict with error)
        if isinstance(result, dict) and result.get('code') == 'INSUFFICIENT_MARGIN':
             logger.error(" MARGIN BLOCKED: Cannot open more positions.")
             # Temporary cooldown for all symbols to avoid spamming
             for s in self.symbols: self.cooldowns[s] = time.time() + 60
             return

        logger.info(f" ENTRY SENT: {result.get('status', 'OK')}")
        
        # 4. Set Safety Stop
        await self.set_safety_stop(symbol, fmt_qty, price, side)
        
        # 5. Cooldown (5 minutes)
        self.cooldowns[symbol] = time.time() + 300 

    async def scan_market(self):
        """Loop contínuo de monitoramento"""
        self.is_running = True
        logger.info(f" FLASH SCALPER RUNNING. Targets: {self.symbols}")
        
        while self.is_running:
            await self.check_existing_positions()
            
            for symbol in self.symbols:
                # Check Cooldown
                if time.time() < self.cooldowns[symbol]:
                    continue
                    
                # Skip if already in position
                if symbol in self.active_positions:
                    continue
                
                try:
                    # 1. Get Depth & OBI
                    depth = self.data.get_orderbook_depth(symbol)
                    if not depth or 'bids' not in depth: continue
                    
                    best_bid = float(depth['bids'][-1][0])
                    best_ask = float(depth['asks'][0][0])
                    mid_price = (best_bid + best_ask) / 2
                    
                    # UPDATE VSC BUFFER FOR ORACLE
                    snapshot = {
                        "symbol": symbol,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "spread": best_ask - best_bid
                    }
                    self.vsc.update_scout_buffer(symbol, snapshot)
                    
                    # OBI Check
                    bid_vol = sum([float(x[1]) for x in depth['bids'][-5:]])
                    ask_vol = sum([float(x[1]) for x in depth['asks'][:5]])
                    total = bid_vol + ask_vol
                    obi = (bid_vol - ask_vol) / total if total > 0 else 0
                    
                    # PRECISION PROTOCOL: Strict OBI + Market Trend Filter
                    # Buy: OBI > 0.6 (Extreme Bull Flow)
                    # Sell: OBI < -0.6 (Extreme Bear Flow)
                    
                    target_side = None
                    if obi > 0.6: target_side = "Buy"
                    elif obi < -0.6: target_side = "Sell"
                    
                    if target_side:
                        logger.info(f" SIGNAL: {symbol} OBI {obi:.2f} -> {target_side}")
                        
                        # Validate with Oracle (Strict Veto)
                        vetoed, reason = self.oracle.veto_signal(symbol, target_side, obi)
                        
                        if not vetoed:
                            # DOUBLE CONFIRMATION: Price Momentum (Simplified)
                            # Only Buy if price is closing near highs (Ask side pressure)
                            # Only Sell if price is closing near lows (Bid side pressure)
                            # Using OBI as proxy for now, but increasing threshold to 0.6 ensures momentum.
                            await self.execute_flash_entry(symbol, target_side, mid_price)
                        else:
                            logger.info(f"    VETOED: {reason}")
                            # Harder Cooldown on Veto (60s) to avoid forcing
                            self.cooldowns[symbol] = time.time() + 60
                            
                except Exception as e:
                    logger.error(f"️ Scan error {symbol}: {e}")
                    
                await asyncio.sleep(0.2) # Micro delay between symbols
            
            await asyncio.sleep(1) # 1s poll interval per cycle

if __name__ == "__main__":
    # Default Targets: HOT ASSETS (High Asymmetry)
    # BEAR WAVES (Short): FOGO (-1.0), APT (-0.49), SUI (-0.42), BNB (-0.41), AAVE (-0.33)
    # BULL WAVES (Long): HYPE (0.94), XLM (0.43), DOGE (0.34), XRP (0.31)
    targets = [
        "FOGO_USDC_PERP", "HYPE_USDC_PERP", 
        "APT_USDC_PERP", "SUI_USDC_PERP", "BNB_USDC_PERP", "AAVE_USDC_PERP",
        "XLM_USDC_PERP", "DOGE_USDC_PERP", "XRP_USDC_PERP",
        "SOL_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP" # Majors always monitored
    ]
    
    scalper = FlashScalper20x(symbols=targets, margin_usd=20.0, leverage=20)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(scalper.scan_market())
    except KeyboardInterrupt:
        logger.info(" FLASH SCALPER STOPPED")
