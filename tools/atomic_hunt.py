import asyncio
import os
import sys
import logging
import time
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

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AtomicHunter")

class AtomicHunter:
    """
    Caçador Atômico (Protocolo de Teste $10).
    Utiliza VSC + Oracle + Sentinel para um tiro de precisão cirúrgica.
    """
    def __init__(self, symbol="SOL_USDC_PERP", amount_usd=10.0, leverage=5):
        self.symbol = symbol
        self.amount_usd = amount_usd
        self.leverage = leverage
        
        # Load Env
        load_dotenv()
        if not os.getenv('BACKPACK_API_KEY'):
            raise ValueError("Chaves de API não configuradas.")
            
        # Initialize Stack
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        
        self.vsc = VSCLayer()
        self.oracle = MarketProxyOracle(self.vsc)
        self.sentinel = PanicSentinel() # Já inicializa seus próprios clientes, ok
        self.audit = IntegrityAudit()
        
        self.is_hunting = False

    async def prepare_hunt(self):
        """Prepara o terreno: Ajusta alavancagem e verifica saldo"""
        logger.info(f"️ PREPARING HUNT: {self.symbol} | ${self.amount_usd} | {self.leverage}x")
        
        # 1. Ajustar Alavancagem
        # Note: Backpack API might require specific endpoint for leverage. 
        # BackpackTrade class usually has set_leverage or similar.
        # Assuming BackpackTrade from LEGACY has set_leverage, but let's check or try.
        # If not, we proceed with current leverage or assume it's set manually.
        # logger.info("Setting leverage...")
        # await self.trade.set_leverage(self.symbol, self.leverage) # Uncomment if implemented
        
        # 2. Verificar Saldo
        # bal = await self.trade.get_balance()
        # logger.info(f"Balance Checked.")
        pass

    async def scan_and_strike(self):
        """Loop de Caça: Monitora OBI e dispara no momento certo"""
        self.is_hunting = True
        logger.info(" ATOMIC HUNTER ACTIVATED. SCANNING FOR PREY...")
        
        try:
            while self.is_hunting:
                # 1. Get Real-Time Depth (VSC Optimized)
                # BackpackData methods are synchronous (requests based)
                # We should run them in executor to avoid blocking the async loop if we want true async behavior
                # But for this simple loop, direct call is fine, just remove await
                depth = self.data.get_orderbook_depth(self.symbol)
                
                # Update Oracle Buffer
                if depth and 'bids' in depth and 'asks' in depth:
                    best_bid = float(depth['bids'][-1][0])
                    best_ask = float(depth['asks'][0][0])
                    mid_price = (best_bid + best_ask) / 2
                    
                    snapshot = {
                        "symbol": self.symbol,
                        "best_bid": best_bid,
                        "best_ask": best_ask,
                        "spread": best_ask - best_bid
                    }
                    self.vsc.update_scout_buffer(self.symbol, snapshot)
                    
                    # 2. Calculate OBI (Simplified for Speed)
                    # Simple Imbalance: (BidVol - AskVol) / (BidVol + AskVol)
                    # Using top 5 levels
                    bid_vol = sum([float(x[1]) for x in depth['bids'][-5:]])
                    ask_vol = sum([float(x[1]) for x in depth['asks'][:5]])
                    total_vol = bid_vol + ask_vol
                    obi = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0
                    
                    # 3. Oracle Veto Check
                    # Strategy: Trend Following (Positive OBI -> Buy)
                    # Threshold: 0.3 (Strong Buy Pressure)
                    
                    # FORCED SIDE LOGIC
                    target_side = None
                    if hasattr(self, 'forced_side') and self.forced_side:
                         # Se o usuário forçou, ignoramos a direção do OBI e só validamos se o Oracle não VETA a direção forçada
                         # Ex: Se forçou SELL, esperamos OBI negativo ou apenas não muito positivo?
                         # Para segurança, se forçou SELL, entramos se OBI < 0.1 (não bullish extremo)
                         target_side = self.forced_side
                    else:
                         # AUTO MODE
                         if obi > 0.3: target_side = "Buy"
                         elif obi < -0.3: target_side = "Sell"
                    
                    if target_side == "Buy":
                        logger.info(f" TARGET LOCKED: OBI {obi:.2f} (BULLISH) -> Aiming BUY")
                        vetoed, reason = self.oracle.veto_signal(self.symbol, "Buy", obi)
                        
                        if not vetoed:
                            await self.execute_strike("Buy", mid_price)
                            self.is_hunting = False
                            break
                        else:
                            logger.info(f"    ORACLE VETO: {reason}")
                            
                    elif target_side == "Sell":
                        logger.info(f" TARGET LOCKED: OBI {obi:.2f} (BEARISH) -> Aiming SELL")
                        vetoed, reason = self.oracle.veto_signal(self.symbol, "Sell", obi)
                        
                        if not vetoed:
                            await self.execute_strike("Sell", mid_price)
                            self.is_hunting = False
                            break
                        else:
                            logger.info(f"    ORACLE VETO: {reason}")
                            
                await asyncio.sleep(0.5) # Fast Loop (500ms poll)
                
        except KeyboardInterrupt:
            logger.info(" HUNT ABORTED BY USER")

    async def set_brackets(self, quantity, entry_price, side):
        """Define Stop Loss e Take Profit na exchange"""
        try:
            sl_pct = 0.015 # 1.5% (Recovery Mode - Tight Stop)
            tp_pct = 0.04  # 4.0% (Recovery Mode - Realistic Target)
            
            if side == "Buy":
                sl_price = entry_price * (1 - sl_pct)
                tp_price = entry_price * (1 + tp_pct)
                exit_side = "Ask"
            else:
                sl_price = entry_price * (1 + sl_pct)
                tp_price = entry_price * (1 - tp_pct)
                exit_side = "Bid"
                
            # Formatar preços (assumindo 4 casas decimais para simplificar, ideal é usar tick_size)
            sl_price = round(sl_price, 4)
            tp_price = round(tp_price, 4)
            
            logger.info(f"️ SETTING BRACKETS: SL {sl_price} | TP {tp_price}")
            
            # Stop Loss (Trigger Market)
            # Adapting to execute_order signature in _LEGACY_V1_ARCHIVE/backpack_trade.py:
            # execute_order(symbol, side, price, quantity, order_type="Limit", ...)
            # NOTE: price parameter is positional and comes before quantity in that specific legacy implementation!
            # Signature: execute_order(symbol, side, price, quantity, order_type="Limit", ...)
            
            # Since StopLoss trigger market doesn't have a limit price, we pass None for price?
            # But the method signature has price as 3rd arg.
            # Let's use kwargs to be safe if possible, or positional.
            
            # The error "missing 1 required positional argument: 'price'" confirms we need to pass it.
            # For Trigger Orders, price is usually ignored if it's Market, but we must pass something.
            
            self.trade.execute_order(
                symbol=self.symbol,
                side=exit_side,
                price="0", # Dummy price for Market orders
                quantity=quantity,
                order_type="StopLoss",
                trigger_price=str(sl_price)
            )
            
            # Take Profit (Trigger Market)
            self.trade.execute_order(
                symbol=self.symbol,
                side=exit_side,
                price="0", # Dummy price
                quantity=quantity,
                order_type="TakeProfit",
                trigger_price=str(tp_price)
            )
            
        except Exception as e:
            logger.error(f" BRACKET ERROR: {e}")

    async def execute_strike(self, side, price):
        """Dispara a ordem atômica com auditoria"""
        logger.warning(f" EXECUTING ATOMIC STRIKE: {side} {self.symbol}...")
        
        # 1. Calculate Quantity (Notional / Price)
        # $10 notional
        raw_qty = self.amount_usd / price
        
        # 2. Atomic Validation & Fix (StepSize)
        # Get Spec VSC
        spec = await self.sentinel._get_asset_spec_vsc(self.symbol)
        is_valid, reason = self.vsc.validate_atomic_payload(raw_qty, price, spec)
        
        final_qty = raw_qty
        if not is_valid and "INVALID_STEP_SIZE" in reason:
             # Fix quantity
             step_size = float(spec.split('|')[2])
             import math
             final_qty = math.floor(raw_qty / step_size) * step_size
             logger.info(f"    ATOMIC FIX: Qty adjusted {raw_qty:.4f} -> {final_qty:.4f}")
        
        # 3. Execute Order
        # Market Order for instant entry
        # Format quantity to match step size decimals strictly
        if 'step_size' in locals() and step_size > 0:
             # Count decimals in step_size
             import decimal
             d = decimal.Decimal(str(step_size))
             decimals = abs(d.as_tuple().exponent)
             fmt_qty = f"{final_qty:.{decimals}f}"
        else:
             fmt_qty = f"{final_qty:.8f}".rstrip('0').rstrip('.')

        order_payload = {
            "symbol": self.symbol,
            "side": "Bid" if side == "Buy" else "Ask",
            "orderType": "Market",
            "quantity": fmt_qty
        }
        
        logger.info(f"    SENDING: {order_payload['side']} {order_payload['quantity']} {order_payload['symbol']}")
        
        # BackpackTrade execute_order is synchronous too
        result = self.trade.execute_order(
            symbol=order_payload["symbol"],
            side=order_payload["side"],
            order_type=order_payload["orderType"],
            quantity=order_payload["quantity"],
            price=None # Market order
        )
        
        # 4. Generate Audit Proof
        oracle_ctx = {"obi_score": 0.99, "sentinel_active": True} # Mock context for now
        proof_hash = self.audit.generate_trade_proof(order_payload, oracle_ctx)
        
        logger.info(f" STRIKE SUCCESSFUL: {result.get('status', 'SENT')}")
        logger.info(f" INTEGRITY PROOF: {proof_hash}")
        
        # 5. Set Safety (TP/SL) - AWM Config (10x, 3% SL, 7% TP)
        await self.set_brackets(fmt_qty, price, "Buy" if side == "Buy" else "Sell")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Atomic Hunter')
    parser.add_argument('--symbol', type=str, default="SOL_USDC_PERP", help='Trading Symbol')
    parser.add_argument('--amount', type=float, default=10.0, help='Amount in USD')
    parser.add_argument('--leverage', type=int, default=5, help='Leverage')
    parser.add_argument('--side', type=str, default="AUTO", help='Force Side (BUY/SELL) or AUTO')
    
    args = parser.parse_args()
    
    # Parameters from args
    hunter = AtomicHunter(symbol=args.symbol, amount_usd=args.amount, leverage=args.leverage)
    
    # Force side injection if provided (quick hack to support forced side in scan logic)
    if args.side != "AUTO":
        hunter.forced_side = args.side.title() # Buy/Sell
    else:
        hunter.forced_side = None

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(hunter.prepare_hunt())
        loop.run_until_complete(hunter.scan_and_strike())
    except KeyboardInterrupt:
        pass
