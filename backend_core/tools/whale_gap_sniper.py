import asyncio
import os
import sys
import logging
import time
import argparse
from typing import List
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from tools.vsc_transformer import VSCLayer
from tools.market_proxy_oracle import MarketProxyOracle
from core.technical_oracle import TechnicalOracle
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from core.backpack_transport import BackpackTransport

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WhaleGapSniper")

class WhaleGapSniper:
    """
    WHALE GAP SNIPER (Assistente Ultra Rápido)
    Detecta e captura Gaps de Baleia (Liquidity Voids) e OBI Spikes.
    Ativação sob demanda para oportunidades de tiro único.
    """
    def __init__(self, symbols: List[str], size_usd: float = 20.0, leverage: int = 10):
        self.symbols = symbols
        self.size_usd = size_usd
        self.leverage = leverage
        self.notional_usd = size_usd * leverage
        
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.transport = BackpackTransport() # Para dados mais rápidos/leves se necessário
        
        # Intelligence Stack
        self.vsc = VSCLayer()
        self.market_oracle = MarketProxyOracle(self.vsc) # Liquidity & Manipulation Check
        self.tech_oracle = TechnicalOracle(self.data) # OBI Calculation
        
        # Compass Majors for Macro Trend
        self.majors = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"]
        self.macro_trend = 0.0 # Neutral

    async def check_macro_compass(self):
        """Verifica a direção macro usando os Majors (Bússola Integrada)"""
        total_obi = 0
        count = 0
        logger.info("Checking Macro Compass...")
        
        for symbol in self.majors:
            try:
                # Usa método síncrono da data lib, mas roda 'rápido'
                depth = self.data.get_orderbook_depth(symbol)
                obi = self.tech_oracle.calculate_obi(depth)
                total_obi += obi
                count += 1
                logger.info(f"   {symbol}: {obi:+.2f}")
            except Exception as e:
                logger.warning(f"   Failed to read {symbol}: {e}")
        
        if count > 0:
            self.macro_trend = total_obi / count
            direction = "BULLISH" if self.macro_trend > 0.1 else ("BEARISH" if self.macro_trend < -0.1 else "NEUTRAL")
            logger.info(f"MACRO TREND: {self.macro_trend:+.2f} [{direction}]")
        else:
            logger.warning("Could not determine macro trend.")

    async def detect_whale_gap(self, symbol: str, depth: dict) -> dict:
        """
        Analisa o Orderbook em busca de Gaps de Baleia ou OBI Extremo.
        Retorna um dicionário de sinal se detectado, ou None.
        """
        if not depth or 'bids' not in depth: return None
        
        # 1. Calculate OBI
        obi = self.tech_oracle.calculate_obi(depth)
        
        # 2. Spread Analysis
        best_bid = float(depth['bids'][-1][0])
        best_ask = float(depth['asks'][0][0])
        mid_price = (best_bid + best_ask) / 2
        spread_pct = (best_ask - best_bid) / best_bid
        
        # 3. Whale Wall Detection (Simplified)
        # Check volume imbalance in top 3 levels vs next 7
        bid_vol_top = sum([float(x[1]) for x in depth['bids'][-3:]])
        ask_vol_top = sum([float(x[1]) for x in depth['asks'][:3]])
        
        signal = None
        
        # CRITÉRIO 1: OBI EXTREMO (Agressão Pura)
        if obi > 0.6: # Super Bullish Imbalance
            signal = {"type": "OBI_SPIKE", "side": "Buy", "score": obi, "price": best_ask}
        elif obi < -0.6: # Super Bearish Imbalance
            signal = {"type": "OBI_SPIKE", "side": "Sell", "score": obi, "price": best_bid}
            
        # CRITÉRIO 2: WHALE GAP (Spread abriu + Movimento rápido)
        # Se spread > 0.1% e OBI confirma direção
        elif spread_pct > 0.001: 
            if obi > 0.3:
                 signal = {"type": "WHALE_GAP_FILL", "side": "Buy", "score": obi, "price": best_ask}
            elif obi < -0.3:
                 signal = {"type": "WHALE_GAP_FILL", "side": "Sell", "score": obi, "price": best_bid}
                 
        return signal

    async def execute_sniper_entry(self, symbol: str, signal: dict):
        """Executa a entrada a mercado instantaneamente"""
        side = signal['side']
        price = signal['price']
        reason = signal['type']
        
        logger.warning(f"SNIPER SHOT: {side} {symbol} | Reason: {reason} | OBI: {signal['score']:.2f}")
        
        # Calculate Quantity
        qty_notional = self.notional_usd
        raw_qty = qty_notional / price
        
        # Precision Adjustment (Hardcoded generic logic for speed, ideally query spec)
        if price < 1.0:
            fmt_qty = f"{int(raw_qty)}" # Low price assets often integer qty
        else:
            fmt_qty = f"{raw_qty:.2f}"
            
        # Execute
        try:
            result = self.trade.execute_order(
                symbol=symbol,
                side="Bid" if side == "Buy" else "Ask",
                order_type="Market",
                quantity=fmt_qty,
                price=None
            )
            logger.info(f"EXECUTION CONFIRMED: {result.get('status', 'SENT')}")
            
            # Set Emergency Stop (Manual Exit Logic, but Safety First)
            sl_pct = 0.02 # 2% Stop for volatility
            sl_price = price * (1 - sl_pct) if side == "Buy" else price * (1 + sl_pct)
            sl_side = "Ask" if side == "Buy" else "Bid"
            
            self.trade.execute_order(
                symbol=symbol,
                side=sl_side,
                order_type="StopLoss",
                quantity=fmt_qty,
                price="0",
                trigger_price=str(round(sl_price, 5))
            )
            logger.info("SAFETY STOP DEPLOYED")
            
        except Exception as e:
            logger.error(f"EXECUTION FAILED: {e}")

    async def hunt(self):
        """Loop de Caça Principal"""
        logger.info(f"WHALE GAP SNIPER ACTIVATED. Targets: {self.symbols}")
        
        # 1. Check Macro First
        await self.check_macro_compass()
        
        # 2. Loop
        try:
            while True:
                for symbol in self.symbols:
                    try:
                        # Get Data
                        depth = self.data.get_orderbook_depth(symbol)
                        
                        # UPDATE VSC BUFFER FOR ORACLE
                        if depth and 'bids' in depth:
                            best_bid = float(depth['bids'][-1][0])
                            best_ask = float(depth['asks'][0][0])
                            snapshot = {
                                "symbol": symbol,
                                "best_bid": best_bid,
                                "best_ask": best_ask,
                                "spread": best_ask - best_bid
                            }
                            self.vsc.update_scout_buffer(symbol, snapshot)
                        
                        # Detect Signal
                        signal = await self.detect_whale_gap(symbol, depth)
                        
                        if signal:
                            # 3. Macro Filter (Don't fight the ocean current unless gap is HUGE)
                            # Se macro é Bullish, evita Shorts fracos. Se Bearish, evita Longs fracos.
                            is_contrarian = (self.macro_trend > 0.1 and signal['side'] == "Sell") or \
                                            (self.macro_trend < -0.1 and signal['side'] == "Buy")
                            
                            # Só permite contra-tendência se o sinal for EXTREMO (Gap de Baleia real)
                            if is_contrarian and abs(signal['score']) < 0.7:
                                logger.info(f"   SKIPPING {symbol} {signal['side']} (Contrarian & Weak OBI {signal['score']:.2f})")
                                continue
                                
                            # PRECISION: Require confirmation of trend direction with Price Action
                            # If Buy, current price must be > previous (or spread stable) - simplified by OBI > 0.5
                            if abs(signal['score']) < 0.5:
                                logger.info(f"   SKIPPING {symbol} (Weak Signal Strength {signal['score']:.2f} < 0.5)")
                                continue

                            # 4. Oracle Veto (Check manipulation)
                            vetoed, reason = self.market_oracle.veto_signal(symbol, signal['side'], signal['score'])
                            
                            if not vetoed:
                                await self.execute_sniper_entry(symbol, signal)
                                # Cooldown or One-Shot? Let's do 10s cooldown per symbol
                                time.sleep(1) 
                            else:
                                logger.info(f"   ORACLE VETO {symbol}: {reason}")
                                
                    except Exception as e:
                        logger.debug(f"Scan error {symbol}: {e}")
                        
                    await asyncio.sleep(0.1) # Fast switch
                
                await asyncio.sleep(0.5) # Loop delay
                
        except KeyboardInterrupt:
            logger.info("SNIPER DEACTIVATED")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Whale Gap Sniper')
    parser.add_argument('--targets', type=str, help='Comma separated symbols (e.g. BTC,SOL)', default="SOL,BTC,ETH")
    parser.add_argument('--size', type=float, default=20.0, help='Margin Size USD')
    parser.add_argument('--leverage', type=int, default=10, help='Leverage')
    
    args = parser.parse_args()
    
    # Parse symbols
    raw_symbols = args.targets.split(',')
    symbols = []
    for s in raw_symbols:
        s = s.strip().upper()
        if not s.endswith("_PERP"): s += "_USDC_PERP"
        symbols.append(s)
        
    sniper = WhaleGapSniper(symbols=symbols, size_usd=args.size, leverage=args.leverage)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sniper.hunt())
