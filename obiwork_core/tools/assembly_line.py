
import os
import sys
import asyncio
import time
import logging
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from funding_hunter import FundingHunter

init(autoreset=True)
load_dotenv()

# Logger Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("VolumeStriker")

class CapitalManager:
    """
    Gerencia o capital com foco em 'Cash Flow Sustentável'.
    Meta por Trade: $0.70 a $5.00 (Lucro Líquido).
    """
    def __init__(self, target_balance=200.0, min_profit=0.70, max_profit=5.00):
        self.target_balance = target_balance
        self.min_profit = min_profit
        self.max_profit = max_profit
        
    def calculate_position_size(self, current_equity, entry_price, sl_price, confidence):
        risk_pct = abs(entry_price - sl_price) / entry_price
        if risk_pct == 0: risk_pct = 0.01
        
        target_profit = self.min_profit
        if confidence >= 80: target_profit = 2.00
        if confidence >= 90: target_profit = 4.00
        
        expected_move = 0.008 
        estimated_fees = 0.002 
        net_move = expected_move - estimated_fees
        
        if net_move <= 0: net_move = 0.001
        
        required_position_size = target_profit / net_move
        
        max_loss_allowable = 5.00
        potential_loss = required_position_size * risk_pct
        
        if potential_loss > max_loss_allowable:
            required_position_size = max_loss_allowable / risk_pct
            
        leverage = required_position_size / current_equity
        
        if leverage > 10:
            required_position_size = current_equity * 10
            
        return required_position_size

    def round_quantity(self, quantity, step_size=None):
        """Helper to round quantity to avoid API errors (1 decimal usually safe for perps)"""
        # If step_size provided, use it. Otherwise default to 1 decimal.
        # But most importantly, Backpack Perps often need 0.1 or 1.0 depending on asset.
        # Let's be safer: 0 decimal for high value, 1 decimal for low value.
        # Or just use 1 decimal as generic safe bet for now.
        # The error "Quantity decimal too long" suggests we are sending too many decimals.
        # Python floats like 304.60000000000002 cause this.
        
        # Force string formatting to 1 decimal place
        return float(f"{quantity:.1f}")

class ProfitMath:
    """
     CALCULADORA DE LUCRO REAL (Fee & Spread Adjusted)
    Garante que o TP de 3% seja LÍQUIDO, cobrindo taxas e spread.
    """
    def __init__(self, maker_fee=0.0003, taker_fee=0.0005): 
        # Estimativas Conservadoras: Maker 0.03%, Taker 0.05%
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee

    def calculate_safe_exit(self, entry_price, side, target_net_pct=0.03):
        """
        Calcula o preço de saída para garantir o lucro líquido alvo.
        Fórmula: 
        Gross Profit Needed = Target Net + EntryFee + ExitFee
        """
        # Se entramos Limit (Maker) e saímos Limit (Maker) = Taxas Mínimas
        # Se saímos Market (Taker) = Taxa Maior
        # Vamos assumir pior caso na saída (Taker) para garantir segurança, 
        # ou Maker se o bot usar PostOnly no TP. O TP do bot é Limit Maker.
        
        total_fees = self.maker_fee + self.maker_fee # Entry Maker + Exit Maker
        
        # Target Bruto = Net + Fees
        gross_target_pct = target_net_pct + total_fees
        
        if side == "Buy": # Long
            exit_price = entry_price * (1 + gross_target_pct)
        else: # Short
            exit_price = entry_price * (1 - gross_target_pct)
            
        return exit_price, total_fees

class VolumeStriker:
    """
     ASSEMBLY LINE AGENT (Volume Farmer)
    
    Roles:
    1. Scout: FundingHunter (Locates Targets)
    2. Ammo: CapitalManager (Prepares Size)
    3. Math: ProfitMath (Calculates Precision Targets)
    4. Sniper: Execution (Enters Trade)
    5. Manager: Auto-Breakeven (Protects Capital)
    """
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.transport = BackpackTransport(self.auth)
        self.data = BackpackData(self.auth)
        self.hunter = FundingHunter()
        self.capital = CapitalManager()
        self.math = ProfitMath()
        self.active_symbol = None
        self.is_managing = False
        
    async def execute_order(self, symbol, side, order_type, quantity, price=None, stop_price=None, post_only=False):
        # Map Side to API Standard (Bid/Ask)
        api_side = "Bid" if side == "Buy" else "Ask"
        if side in ["Bid", "Ask"]: api_side = side
        
        # API Compatibility: Map "StopMarket" to "Market" + triggerPrice
        if order_type == "StopMarket":
            order_type = "Market"
            if not stop_price: logger.warning("️ StopMarket requested but no stop_price provided!")
            
        # API Compatibility: Map "StopLimit" to "Limit" + triggerPrice
        if order_type == "StopLimit":
            order_type = "Limit"
            if not stop_price: logger.warning("️ StopLimit requested but no stop_price provided!")

        endpoint = "/api/v1/order"
        payload = {
            "symbol": symbol,
            "side": api_side,
            "orderType": order_type,
            "quantity": str(quantity),
            "selfTradePrevention": "RejectTaker"
        }
        
        if price: payload["price"] = str(price)
        if stop_price: payload["triggerPrice"] = str(stop_price)
        if order_type == "Limit": payload["timeInForce"] = "GTC"
        if post_only: payload["postOnly"] = True
        
        logger.info(f" FIRE: {side} {quantity} {symbol} @ {price or 'Market'} (Stop={stop_price})")
        return self.transport._send_request("POST", endpoint, "orderExecute", payload)

    async def cancel_orders(self, symbol, order_id=None):
        endpoint = "/api/v1/order" if order_id else "/api/v1/orders"
        payload = {"symbol": symbol}
        if order_id: 
            payload["orderId"] = order_id
            instruction = "orderCancel"
        else:
            instruction = "orderCancelAll"
            
        logger.info(f" Canceling orders for {symbol} ({order_id or 'All'})")
        return self.transport._send_request("DELETE", endpoint, instruction, payload)

    async def manage_active_trade(self):
        """
        ️ TRADE MANAGER AGENT
        Monitora PnL e move Stop para o Lucro (Auto-Breakeven).
        """
        try:
            positions = self.transport.get_positions()
            if not positions:
                self.active_symbol = None
                return

            for pos in positions:
                # Debug Keys if needed
                # logger.info(f"Position Keys: {pos.keys()}")
                
                symbol = pos['symbol']
                # Try common keys for quantity
                qty = 0.0
                if 'quantity' in pos: qty = float(pos['quantity'])
                elif 'netQuantity' in pos: qty = float(pos['netQuantity'])
                elif 'amount' in pos: qty = float(pos['amount'])
                else:
                    logger.warning(f"Quantity key not found in position: {pos.keys()}")
                    continue
                    
                entry_price = float(pos.get('entryPrice', 0))
                mark_price = float(pos.get('markPrice', 0))
                side = pos.get('side', 'Long') # Default or check netQuantity sign
                
                if qty == 0: continue
                
                self.active_symbol = symbol
                
                # PnL Calculation
                if side == "Long":
                    pnl_pct = (mark_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - mark_price) / entry_price
                    
                logger.info(f" MONITOR: {symbol} | PnL: {pnl_pct*100:.4f}% | Entry: {entry_price}")
                
                #  LOGIC: AUTO-BREAKEVEN (STOP GAIN)
                # Se lucro > 0.5% (cobre taxas + lucro minimo), move Stop para Entry + 0.1%
                activation_threshold = 0.005 # 0.5%
                secure_profit = 0.001 # 0.1%
                
                if pnl_pct > activation_threshold:
                    # Check if we already have a Stop Order at the right price
                    open_orders = self.transport.get_open_orders(symbol)
                    
                    target_stop_price = 0.0
                    if side == "Long":
                        target_stop_price = entry_price * (1 + secure_profit)
                    else:
                        target_stop_price = entry_price * (1 - secure_profit)
                        
                    # Verifica se já existe stop configurado corretamente
                    stop_exists = False
                    for order in open_orders:
                        if order['orderType'] in ['StopLimit', 'StopMarket']:
                            trigger = float(order.get('triggerPrice', 0))
                            # Se já existe um stop IGUAL ou MELHOR (mais alto pra Long), ok
                            if side == "Long" and trigger >= target_stop_price:
                                stop_exists = True
                            elif side == "Short" and trigger <= target_stop_price:
                                stop_exists = True
                    
                    if not stop_exists:
                        logger.info(f" LOCKING PROFIT! Moving Stop to {target_stop_price}")
                        # 1. Cancel Old Stops
                        await self.cancel_orders(symbol)
                        
                        # 2. Place New Stop Gain
                        stop_side = "Sell" if side == "Long" else "Buy"
                        # Usando StopMarket para garantir saída
                        await self.execute_order(symbol, stop_side, "StopMarket", abs(qty), stop_price=target_stop_price)

        except Exception as e:
            logger.error(f"Manager Error: {e}")

    async def get_market_filters(self, symbol):
        """Helper to get tick size and step size dynamically"""
        try:
            markets = self.data.get_markets()
            for m in markets:
                if m['symbol'] == symbol:
                    filters = m.get('filters', {})
                    price_filter = filters.get('price', {})
                    qty_filter = filters.get('quantity', {})
                    
                    return {
                        'tickSize': float(price_filter.get('tickSize', m.get('tickSize', 0.01))),
                        'stepSize': float(qty_filter.get('stepSize', m.get('stepSize', 1.0))) # Default to 1.0 if unknown
                    }
            return {'tickSize': 0.01, 'stepSize': 1.0}
        except:
            return {'tickSize': 0.01, 'stepSize': 1.0}

    async def get_tick_size(self, symbol):
        filters = await self.get_market_filters(symbol)
        return filters['tickSize']

    async def execute_smart_chase(self, symbol, side, quantity, max_retries=5, aggression=0.9):
        """
         SMART MAKER CHASE (LimitChaser)
        Equation: EntryPrice = BestBid + (Spread * Aggression)
        Goal: Maker Execution (PostOnly)
        """
        print(f"{Fore.MAGENTA} INITIATING SMART MAKER CHASE: {symbol} ({side}){Style.RESET_ALL}")
        
        tick_size = await self.get_tick_size(symbol)
        
        for attempt in range(max_retries):
            # 1. Read Book
            depth = self.data.get_orderbook_depth(symbol)
            if not depth or not depth.get('bids') or not depth.get('asks'):
                print("   ️ Empty Book. Retrying...")
                await asyncio.sleep(1)
                continue
                
            best_bid = float(depth['bids'][-1][0]) # Backpack: Bids are ASC, last is highest
            best_ask = float(depth['asks'][0][0])  # Backpack: Asks are ASC, first is lowest
            spread = best_ask - best_bid
            
            # 2. Calculate Smart Price
            target_price = 0.0
            
            if side == "Buy":
                # Formula: BestBid + (Spread * k)
                raw_price = best_bid + (spread * aggression)
                # Cap at BestAsk - 1 tick (Never cross spread)
                limit_cap = best_ask - tick_size
                target_price = min(raw_price, limit_cap)
            else: # Sell
                # Formula: BestAsk - (Spread * k)
                raw_price = best_ask - (spread * aggression)
                # Floor at BestBid + 1 tick
                limit_floor = best_bid + tick_size
                target_price = max(raw_price, limit_floor)
                
            # Round to tick size
            import decimal
            # Safer precision calculation
            d_tick = decimal.Decimal(str(tick_size))
            precision = abs(d_tick.as_tuple().exponent)
            
            target_price = round(target_price / tick_size) * tick_size
            # Fixed f-string precision format
            fmt = f"{{:.{precision}f}}"
            target_price = float(fmt.format(target_price))
            
            print(f"    Attempt {attempt+1}/{max_retries}: {side} @ {target_price} (Spread: {spread:.4f})")
            
            # 3. Send Limit PostOnly
            res = await self.execute_order(symbol, side, "Limit", quantity, price=target_price, post_only=True)
            
            if not res:
                print("   ️ Order Rejected (Likely Crossed Book). Retrying...")
                await asyncio.sleep(1)
                continue
                
            # 4. Monitor Execution
            # Wait 2s for fill
            await asyncio.sleep(2)
            
            # Check Status
            open_orders = self.transport.get_open_orders(symbol)
            is_open = False
            my_order_id = None
            
            # Find our order (assuming it's the one we just sent, checking price match approximately)
            # Better: execute_order should return order ID. But _send_request returns JSON.
            # If res contains ID, use it.
            if isinstance(res, dict) and 'id' in res:
                my_order_id = res['id']
                
            if my_order_id:
                # Check specific order
                # If not in open_orders, it's filled or canceled.
                # Since we didn't cancel, it must be filled.
                order_found = False
                for o in open_orders:
                    if o['id'] == my_order_id:
                        is_open = True
                        break
                
                if not is_open:
                    print(f"    SURGICAL EXECUTION CONFIRMED (Maker).")
                    return True
                else:
                    print(f"   ️ Price Moved. Canceling to adjust...")
                    await self.cancel_orders(symbol, order_id=my_order_id)
            else:
                # Fallback if no ID returned
                print("   ️ No Order ID. Assuming failed.")
                
        print(f"    FAILED Maker Capture after {max_retries} attempts.")
        return False

    async def get_ma_levels(self, symbol, interval="1m", limit=50):
        """
         MA ORACLE
        Calculates EMA(9) and EMA(20) to find the 'Exact Place'.
        """
        try:
            import pandas as pd
            klines = self.transport.get_klines(symbol, interval, limit)
            if not klines: return None
            
            # Backpack Kline: [start, open, high, low, close, volume, ...]
            # We need Close prices (index 4)
            closes = [float(k['close']) for k in klines] # Dict access if using get_klines from transport which calls json()
            
            if len(closes) < 20: return None
            
            df = pd.DataFrame({'close': closes})
            df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
            
            last_ema9 = df['ema9'].iloc[-1]
            last_ema20 = df['ema20'].iloc[-1]
            last_close = df['close'].iloc[-1]
            
            return {
                'ema9': last_ema9,
                'ema20': last_ema20,
                'close': last_close,
                'trend': 'Bullish' if last_ema9 > last_ema20 else 'Bearish'
            }
        except Exception as e:
            logger.error(f"MA Calc Error: {e}")
            return None

    async def execute_ma_smart_entry(self, symbol, side, quantity, max_retries=5, stop_loss_price=None):
        """
         EXACT MA ENTRY (With Atomic Stop Loss)
        Uses Moving Average as the Anchor for Limit Order.
        If Long: Limit Price = EMA 9 (Dynamic Support).
        """
        print(f"{Fore.BLUE} CALCULATING EXACT MA ENTRY: {symbol} ({side}){Style.RESET_ALL}")
        
        tick_size = await self.get_tick_size(symbol)
        
        # 1. Get MA Levels
        levels = await self.get_ma_levels(symbol)
        if not levels:
            print("   ️ MA Data Unavailable. Fallback to Smart Chase.")
            return await self.execute_smart_chase(symbol, side, quantity, max_retries)
            
        ema9 = levels['ema9']
        close = levels['close']
        trend = levels['trend']
        
        print(f"    ANALYSIS: Price ${close:.4f} | EMA9 ${ema9:.4f} | Trend: {trend}")
        
        # 2. Determine Exact Limit Price
        target_price = 0.0
        
        if side == "Buy":
            dist_pct = (close - ema9) / close
            if dist_pct > 0.002: # 0.2% above EMA
                target_price = close - (close - ema9) * 0.3 # 30% pullback
            else:
                target_price = ema9
            # Cap at Best Ask
            depth = self.data.get_orderbook_depth(symbol)
            if depth and depth.get('asks'):
                best_ask = float(depth['asks'][0][0])
                if target_price >= best_ask: target_price = best_ask - tick_size
                
        else: # Sell
            dist_pct = (ema9 - close) / close
            if dist_pct > 0.002:
                target_price = close + (ema9 - close) * 0.3
            else:
                target_price = ema9
            # Floor at Best Bid
            depth = self.data.get_orderbook_depth(symbol)
            if depth and depth.get('bids'):
                best_bid = float(depth['bids'][-1][0])
                if target_price <= best_bid: target_price = best_bid + tick_size
        
        # Rounding
        import decimal
        d_tick = decimal.Decimal(str(tick_size))
        precision = abs(d_tick.as_tuple().exponent)
        fmt = f"{{:.{precision}f}}"
        target_price = float(fmt.format(round(target_price / tick_size) * tick_size))
        
        print(f"    EXACT LIMIT LOCATION FOUND: ${target_price}")
        
        # 3. Execute Loop
        for attempt in range(max_retries):
            # Refresh Book for Cap Check (Dynamic)
            depth = self.data.get_orderbook_depth(symbol)
            if not depth: continue
            
            # Re-verify we aren't crossing spread (Market)
            if side == "Buy":
                best_ask = float(depth['asks'][0][0])
                if target_price >= best_ask: 
                    target_price = best_ask - tick_size
                    target_price = float(fmt.format(round(target_price / tick_size) * tick_size))
            else:
                best_bid = float(depth['bids'][-1][0])
                if target_price <= best_bid:
                    target_price = best_bid + tick_size
                    target_price = float(fmt.format(round(target_price / tick_size) * tick_size))

            print(f"    Attempt {attempt+1}/{max_retries}: {side} @ {target_price}")
            
            # ATOMIC STOP LOSS: If API supports triggers in OrderExecute (which it does via triggerPrice for Stops, 
            # but for Limits usually it's separate unless 'stopLossTriggerPrice' is used).
            # We will try to attach it if supported, otherwise we must send it immediately after.
            # Backpack API docs suggest atomic SL on open might not be standard in v1 yet.
            # So we stick to "Send Limit -> Wait Fill -> Send Stop".
            
            res = await self.execute_order(symbol, side, "Limit", quantity, price=target_price, post_only=True)
            
            if not res:
                if side == "Buy": target_price -= tick_size
                else: target_price += tick_size
                target_price = float(fmt.format(target_price))
                print(f"   ️ Rejected. Backing off to {target_price}...")
                await asyncio.sleep(1)
                continue
                
            await asyncio.sleep(2)
            
            # Check Fill
            open_orders = self.transport.get_open_orders(symbol)
            is_open = False
            my_order_id = res.get('id') if isinstance(res, dict) else None
            
            if my_order_id:
                for o in open_orders:
                    if o['id'] == my_order_id:
                        is_open = True
                        break
                if not is_open:
                    print("    MA LIMIT FILLED.")
                    # CRITICAL: Send Stop Loss IMMEDIATELY
                    if stop_loss_price:
                        print(f"   ️ ATTACHING STOP LOSS @ {stop_loss_price}...")
                        stop_side = "Sell" if side == "Buy" else "Buy"
                        await self.execute_order(symbol, stop_side, "StopMarket", quantity, stop_price=stop_loss_price)
                    return True
                else:
                    print("   ⏳ Order Resting at MA... (Waiting 2s)")
                    await asyncio.sleep(2)
                    
                    open_orders = self.transport.get_open_orders(symbol)
                    is_open_2 = False
                    for o in open_orders:
                        if o['id'] == my_order_id: is_open_2 = True
                        
                    if not is_open_2:
                        print("    FILLED.")
                        if stop_loss_price:
                            print(f"   ️ ATTACHING STOP LOSS @ {stop_loss_price}...")
                            stop_side = "Sell" if side == "Buy" else "Buy"
                            await self.execute_order(symbol, stop_side, "StopMarket", quantity, stop_price=stop_loss_price)
                        return True
                    else:
                        print("   ️ Price moving away. Canceling to Re-Assess.")
                        await self.cancel_orders(symbol, order_id=my_order_id)
            
        return False

    async def safety_net_check(self):
        """
        ️ SAFETY NET: Redundant Stop Loss Check
        Scans ALL open positions. If any has no Stop Loss order, it PLACES ONE IMMEDIATELY.
        """
        try:
            positions = self.transport.get_positions()
            if not positions: return

            open_orders = self.transport.get_open_orders()
            
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
                if qty == 0: continue
                
                entry_price = float(pos.get('entryPrice', 0))
                side = pos.get('side', 'Long')
                
                # Check if this symbol has a Stop Order
                has_stop = False
                if open_orders:
                    for o in open_orders:
                        if o['symbol'] == symbol and o['orderType'] in ['StopLimit', 'StopMarket']:
                            has_stop = True
                            break
                
                if not has_stop:
                    print(f"{Fore.RED} SAFETY NET TRIGGERED: {symbol} has NO STOP LOSS! Placing Emergency Stop...{Style.RESET_ALL}")
                    
                    # Place Emergency Hard Stop (1.5% from Entry)
                    sl_pct = 0.015
                    stop_price = entry_price * (1 - sl_pct) if side == "Long" else entry_price * (1 + sl_pct)
                    
                    # Round price
                    tick_size = await self.get_tick_size(symbol)
                    import decimal
                    d_tick = decimal.Decimal(str(tick_size))
                    precision = abs(d_tick.as_tuple().exponent)
                    stop_price = round(stop_price, precision)
                    
                    stop_side = "Sell" if side == "Long" else "Buy"
                    
                    # Fire Emergency Stop
                    await self.execute_order(symbol, stop_side, "StopMarket", abs(qty), stop_price=stop_price)
                    print(f"   ️ Emergency Stop Placed @ {stop_price}")
                    
        except Exception as e:
            logger.error(f"Safety Net Error: {e}")

    async def manage_take_profit(self):
        """
         TAKE PROFIT MANAGER
        Monitors active positions and places TP orders if they don't exist.
        Goal: Secure 0.8% - 1.2% profit.
        """
        try:
            positions = self.transport.get_positions()
            if not positions: return

            open_orders = self.transport.get_open_orders()
            
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
                if qty == 0: continue
                
                entry_price = float(pos.get('entryPrice', 0))
                side = pos.get('side', 'Long')
                
                # Check if this symbol has a TP Order (Limit or TakeProfit)
                has_tp = False
                if open_orders:
                    for o in open_orders:
                        # Standard Limit orders can be TPs if they are ReduceOnly or opposite side above price
                        if o['symbol'] == symbol:
                            if o['orderType'] in ['TakeProfit', 'TakeProfitLimit']:
                                has_tp = True
                                break
                            # Or a simple Limit Sell above entry (for Long)
                            if o['orderType'] == 'Limit':
                                limit_price = float(o.get('price', 0))
                                if side == "Long" and limit_price > entry_price: has_tp = True
                                elif side == "Short" and limit_price < entry_price: has_tp = True
                
                if not has_tp:
                    print(f"{Fore.GREEN} PLACING TAKE PROFIT: {symbol}{Style.RESET_ALL}")
                    
                    # Target 1.2%
                    tp_pct = 0.012
                    tp_price = entry_price * (1 + tp_pct) if side == "Long" else entry_price * (1 - tp_pct)
                    
                    # Round price
                    tick_size = await self.get_tick_size(symbol)
                    import decimal
                    d_tick = decimal.Decimal(str(tick_size))
                    precision = abs(d_tick.as_tuple().exponent)
                    tp_price = round(tp_price, precision)
                    
                    tp_side = "Sell" if side == "Long" else "Buy"
                    
                    # Place Limit Maker TP
                    await self.execute_order(symbol, tp_side, "Limit", abs(qty), price=tp_price, post_only=True)
                    print(f"    TP Set @ {tp_price}")
                    
        except Exception as e:
            logger.error(f"TP Manager Error: {e}")

    async def run_golden_sniper_cycle(self):
        """
         GOLDEN SNIPER PROTOCOL
        - Assets: BTC & SOL Only (High Liquidity)
        - Leverage: 3x (Sleep Safe)
        - Entry: Limit at EMA20 (1H) - "Pescando no Suporte"
        - Exit: Trailing Stop (No fixed TP limit, let it run)
        """
        print(f"\n{Fore.YELLOW} GOLDEN SNIPER PROTOCOL ACTIVE (BTC/SOL Only)...{Style.RESET_ALL}")
        
        # 0. HOUSEKEEPING
        await self.safety_net_check()
        # await self.manage_take_profit() # Disabled Fixed TP Manager in favor of Trailing Logic?
        # Actually, let's keep a hard TP at +5% just in case of moonshot, but Trailing is better.
        # Let's use a custom manager for this mode.
        
        # 1. SCOUT (Restricted + Blue Chips)
        # Expanded List: BTC, SOL, ETH, DOGE, SUI, LINK, AVAX
        targets = ["SOL_USDC", "BTC_USDC", "ETH_USDC", "DOGE_USDC", "SUI_USDC", "LINK_USDC", "AVAX_USDC"]
        
        for target in targets:
            # Check Position
            positions = self.transport.get_positions()
            in_pos = False
            for p in positions:
                if p['symbol'] == target and float(p.get('quantity', 0)) != 0:
                    in_pos = True
                    # TRAILING STOP LOGIC
                    await self.manage_trailing_stop(target, p)
                    break
            
            if in_pos: 
                print(f"   ️ Managing {target} Position...")
                continue

            # 2. ANALYZE (1H Trend & EMA Levels)
            print(f"    Analyzing {target} Structure...")
            ma_data = await self.get_ma_levels(target, interval="1h", limit=50)
            if not ma_data: continue
            
            trend = ma_data['trend']
            close = ma_data['close']
            ema20 = ma_data['ema20']
            
            # Distance to EMA20
            dist_to_ema = (close - ema20) / close
            
            # Logic: We want to BUY near EMA20 in Bull Trend
            # or SELL near EMA20 in Bear Trend.
            # "Pescando no Suporte"
            
            bias = "Neutral"
            entry_price = 0.0
            
            if trend == "Bullish":
                # Entry = EMA20 (Support)
                entry_price = ema20
                # Only if price is reasonably close (within 2%) to avoid waiting forever?
                # Or just place it and wait. User said "pescando".
                if dist_to_ema > 0 and dist_to_ema < 0.05: # Within 5% range
                    bias = "Long"
            elif trend == "Bearish":
                entry_price = ema20
                if dist_to_ema < 0 and abs(dist_to_ema) < 0.05:
                    bias = "Short"
            
            if bias == "Neutral":
                print(f"     Skipping {target}: Trend Unclear or Too Far from EMA.")
                continue

            print(f"    SETTING TRAP: {target} ({bias}) @ ${entry_price:.2f}")

            # 3. PREPARE AMMO (Higher Allocation, Low Lev)
            # "Foco em 1 ou 2 Ativos" -> Use 20% of Equity per trade (Allows ~5 positions max)
            # Expanded list means we need to reduce per-trade allocation to avoid full margin on just 2 assets.
            collateral = self.transport.get_account_collateral()
            equity = 100.0
            if collateral and isinstance(collateral, dict):
                 equity = float(collateral.get('totalPortfolioValue', collateral.get('equity', 100.0)))
            
            allocation_equity = equity * 0.20 
            
            # Leverage 3x
            leverage = 3.0
            notional = allocation_equity * leverage
            
            # 4. EXECUTE (Limit Maker at EMA20)
            # Check if we already have open orders for this
            open_orders = self.transport.get_open_orders(target)
            has_trap = False
            for o in open_orders:
                if o['orderType'] == 'Limit':
                    has_trap = True
                    # Optional: Update price if EMA moved significantly?
                    # For now, let's just assume if order exists, trap is set.
            
            if has_trap:
                print(f"     Trap already set for {target}. Waiting...")
                continue
            
            # Place Order
            ticker = self.data.get_ticker(target)
            current_price = float(ticker['lastPrice'])
            
            # Calc Quantity
            quantity_usd = notional
            
            # Rounding
            filters = await self.get_market_filters(target)
            step_size = filters['stepSize']
            tick_size = filters['tickSize']
            
            import math
            raw_qty = quantity_usd / entry_price # Use Entry Price for Calc
            quantity = math.floor(raw_qty / step_size) * step_size
            if step_size < 1:
                decimals = int(abs(math.log10(step_size)))
                quantity = float(f"{quantity:.{decimals}f}")
            else:
                quantity = int(quantity)
                
            # Round Entry Price
            import decimal
            d_tick = decimal.Decimal(str(tick_size))
            precision = abs(d_tick.as_tuple().exponent)
            entry_price = round(entry_price, precision)
            
            side = "Buy" if bias == "Long" else "Sell"
            
            print(f"    PLACING LIMIT: {side} {quantity} {target} @ {entry_price}")
            # API FIX: Use "Market" with triggerPrice/Quantity
            # Correct payload for Stop Market in Backpack V1
            stop_payload = {
                "symbol": target,
                "side": "Sell" if side == "Buy" else "Buy",
                "orderType": "Market",
                "quantity": str(quantity),
                "triggerPrice": str(sl_price),
                "triggerQuantity": str(quantity)
            }
            
            # We send this AS SOON as Limit fills.
            # But here we are just placing the Limit.
            # The Safety Net will pick it up.
            # However, user wants "EXPRESSAMENTE NAO OPERAR SEM SL".
            # Can we send the Stop Order NOW?
            # If we send Stop Market now, and we have no position, it might be rejected or sit as a trigger to OPEN a position?
            # Backpack Trigger Orders can open positions.
            # If we send a Sell Stop Market below current price, it triggers immediately if price drops.
            # This is risky if our Limit Buy hasn't filled yet.
            # SO: The only safe way is to attach it AFTER fill.
            # We rely on Safety Net (which we just tested and works).
            
            res = await self.execute_order(target, side, "Limit", quantity, price=entry_price, post_only=True)
            
            if res and isinstance(res, dict) and 'id' in res:
                print(f"    LIMIT ACCEPTED. Watching for Fill to attach SL...")
                # We can't attach SL to a resting limit easily without OCO.
                # So we rely on the 'manage_trailing_stop' and 'safety_net_check' which run every cycle.
                # To be EXTRA SAFE, we will run safety_net_check() immediately after this loop.
            else:
                print(f"    Limit Rejected.")

    async def safety_net_check(self):
        """
        ️ SAFETY NET: Redundant Stop Loss Check (CRITICAL)
        Scans ALL open positions. If any has no Stop Loss order, it PLACES ONE IMMEDIATELY.
        """
        try:
            positions = self.transport.get_positions()
            if not positions: return

            open_orders = self.transport.get_open_orders()
            
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
                if qty == 0: continue
                
                entry_price = float(pos.get('entryPrice', 0))
                side = pos.get('side', 'Long')
                
                # Check if this symbol has a Stop Order
                has_stop = False
                if open_orders:
                    for o in open_orders:
                        if o['symbol'] == symbol and o['orderType'] in ['StopLimit', 'StopMarket']:
                            has_stop = True
                            break
                
                if not has_stop:
                    print(f"{Fore.RED} CRITICAL WARNING: {symbol} HAS NO STOP LOSS! PLACING EMERGENCY STOP NOW!{Style.RESET_ALL}")
                    
                    # Place Emergency Hard Stop (1.5% from Entry)
                    sl_pct = 0.015
                    stop_price = entry_price * (1 - sl_pct) if side == "Long" else entry_price * (1 + sl_pct)
                    
                    # Round price
                    tick_size = await self.get_tick_size(symbol)
                    import decimal
                    d_tick = decimal.Decimal(str(tick_size))
                    precision = abs(d_tick.as_tuple().exponent)
                    stop_price = round(stop_price, precision)
                    
                    stop_side = "Sell" if side == "Long" else "Buy"
                    
                    # FIX: Use "Market" with triggerPrice/Quantity (Backpack V1 Standard)
                    endpoint = "/api/v1/order"
                    payload = {
                        "symbol": symbol,
                        "side": stop_side,
                        "orderType": "Market",
                        "quantity": str(abs(qty)),
                        "triggerPrice": str(stop_price),
                        "triggerQuantity": str(abs(qty)),
                        "selfTradePrevention": "RejectTaker"
                    }
                    
                    print(f"   ️ EMERGENCY STOP PLACED @ {stop_price}")
                    await self.transport._send_request("POST", endpoint, "orderExecute", payload)
                    
        except Exception as e:
            logger.error(f"Safety Net Error: {e}")

async def main():
    striker = VolumeStriker()
    print(f"{Fore.YELLOW} GOLDEN SNIPER PROTOCOL (BTC/SOL ONLY | EMA20 ENTRY) INITIALIZED.{Style.RESET_ALL}")
    
    while True:
        try:
            await striker.run_golden_sniper_cycle()
            
            print(f" Scanning Horizon... (Next check in 60s)")
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"CRITICAL SNIPER ERROR: {e}")
            print(f"️ Retrying in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    while True: # Outer Loop for Hard Crash Recovery
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print(" Night Owl Halted Manually.")
            break
        except Exception as e:
             print(f" FATAL ERROR: {e}. REBOOTING PROCESS...")
             time.sleep(10)
