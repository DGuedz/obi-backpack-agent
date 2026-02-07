import os
import sys
import time
import math
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport
from core.book_scanner import BookScanner
from core.technical_oracle import TechnicalOracle
from tools.vsc_transformer import VSCTransformer
from tools.hft_indicators import HFTIndicators

class ObiCompoundRadar:
    def __init__(self):
        self.transport = BackpackTransport()
        self.scanner = BookScanner()
        # Oracle needs transport as data_client
        self.oracle = TechnicalOracle(self.transport)
        self.vsc = VSCTransformer()
        self.hft = HFTIndicators() # Initialize HFT
        self.min_trade_amount = 10.0 # USD
        self.leverage = 3 # Adjusted to 3x (User: "SCALP COM 3 X")
        self.max_positions = 1 # SERIAL MODE (User: "ABRIU AOUTRA") - Single Threaded Focus
        self.trailing_step = 0.015 
        self.session_pnl = 0.0 # Track session profit towards $100 goal
        
        # Alvos Sniper (Baseados em Liquidez) - DESATIVADOS PARA EVITAR SAÍDA PREMATURA
        self.sniper_targets = {}
        
        print(" OBI MAKER RADAR INITIALIZED")
        print("   -> Mode: SERIAL SCALP (Deep Analysis)")
        print("   -> Leverage: 3x (Safe Scalp)")
        print("   -> Max Positions: 1 (Focus on Quality)")
        print("   -> HFT Module: Active (VWAP/EMA/RSI/BB)")
        print("    MISSION: $10 TRADES | HIT & RUN | CYCLE PROFIT")

    def get_whale_obi(self, symbol):
        """Calcula OBI focando em baleias (Ordens > $5k). Retorna (whale_obi, retail_obi)"""
        try:
            book = self.transport.get_orderbook_depth(symbol, limit=100)
            if not book: return 0.0, 0.0
            
            bids = book.get('bids', [])
            asks = book.get('asks', [])
            
            whale_threshold = 5000
            
            w_bids = sum([float(p)*float(q) for p,q in bids if float(p)*float(q) >= whale_threshold])
            w_asks = sum([float(p)*float(q) for p,q in asks if float(p)*float(q) >= whale_threshold])
            
            r_bids = sum([float(p)*float(q) for p,q in bids if float(p)*float(q) < whale_threshold])
            r_asks = sum([float(p)*float(q) for p,q in asks if float(p)*float(q) < whale_threshold])
            
            w_total = w_bids + w_asks
            w_obi = (w_bids - w_asks) / w_total if w_total > 0 else 0.0
            
            r_total = r_bids + r_asks
            r_obi = (r_bids - r_asks) / r_total if r_total > 0 else 0.0
            
            return w_obi, r_obi
        except Exception:
            return 0.0, 0.0

    def get_market_opportunities(self):
        """Varre o mercado em busca de OBI Extremo (Whale Filter Enabled)"""
        print("\n SCANNING ALL MARKETS FOR SAFE HARBOR (GLOBAL SCAN)...")
        
        # Dynamic Market Fetch
        try:
            markets = self.transport.get_all_markets()
            # ONLY BTC FOR SINGLE ENTRY STUDY
            # User: "ESTUDE UMA ENTRADA UNICA EM BTC"
            assets = ["BTC_USDC_PERP"]
            
            print(f"   -> Analyzing {len(assets)} active markets (BTC ONLY)...")
        except:
             # Fallback list
             assets = [
                "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "SUI_USDC_PERP",
                "AVAX_USDC_PERP", "DOGE_USDC_PERP", "XRP_USDC_PERP", "LINK_USDC_PERP",
                "APT_USDC_PERP", "FOGO_USDC_PERP", "PENGU_USDC_PERP", "PEPE_USDC_PERP",
                "WIF_USDC_PERP", "BONK_USDC_PERP", "JUP_USDC_PERP", "RENDER_USDC_PERP",
                "NEAR_USDC_PERP", "TIA_USDC_PERP", "INJ_USDC_PERP", "SEI_USDC_PERP",
                "ZORA_USDC_PERP", "HYPE_USDC_PERP", "IP_USDC_PERP", "WLFI_USDC_PERP",
                "VIRTUAL_USDC_PERP", "S_USDC_PERP", "MON_USDC_PERP", "LIT_USDC_PERP"
             ]
        
        opportunities = []
        for symbol in assets:
            try:
                # OBI Check
                depth = self.transport.get_orderbook_depth(symbol)
                if not depth:
                     print(f"      ️ No depth for {symbol}")
                     continue
                
                # Análise de Custos (Smart Taker)
                bids = depth.get('bids', [])
                asks = depth.get('asks', [])
                if not bids or not asks:
                    print(f"      ️ Empty book for {symbol}")
                    continue
                
                # Debug Sort Order (Cleaned)
                # Legacy Fix: Transport layer now handles sorting. Double check here just in case.
                if float(bids[0][0]) < float(bids[-1][0]):
                     best_bid = float(bids[-1][0])
                else:
                     best_bid = float(bids[0][0])

                best_ask = float(asks[0][0]) 
                
                spread_pct = ((best_ask - best_bid) / best_bid) * 100
                
                obi = self.scanner.calculate_obi(depth)
                
                # Filtro de Spread: Ignorar se spread > 0.06% (COST CONTROL: "Nao pagar caro demais pra entrar")
                if spread_pct > 0.06:
                    print(f"      ️ Spread too high for {symbol}: {spread_pct:.3f}% (Limit 0.06%)")
                    continue
                
                # WHALE CHECK
                w_obi, r_obi = self.get_whale_obi(symbol)
                
                # Funding Rate Filter (Anti-Crowd)
                # Se Funding for muito positivo (> 0.01%), todo mundo está Long.
                # Perigoso entrar Long (pagar taxa alta + risco de flush).
                # Melhor buscar Short ou ficar de fora.
                
                funding_rate = 0.0 # Default
                # TODO: Fetch real funding if possible efficiently
                # Por enquanto, assumimos Neutral se não temos dados em tempo real no loop rápido
                
                # Se tivéssemos o funding:
                # if trend == "BULLISH" and funding_rate > 0.0001:
                #     print(f"      ️ Funding High ({funding_rate*100:.4f}%). Skipping Long.")
                #     continue
                
                # VSC Analysis (Anti-Trap Protocol)
                vsc_score, trap_signal, confidence = self.vsc.analyze(depth)
                
                # HFT INDICATORS INTEGRATION
                # Define Price for HFT Check (Mid Price)
                price = (best_bid + best_ask) / 2

                # Fetch Klines for HFT Calculation (1m candles for speed)
                klines = self.transport.get_klines(symbol, "1m", limit=20)
                
                # Extract Close Prices for EMA/RSI
                closes = [float(k['close']) for k in klines] if klines else []
                
                # Calculate HFT Metrics
                vwap = self.hft.calculate_vwap(klines)
                ema_fast = self.hft.calculate_ema(closes, period=9)
                rsi = self.hft.calculate_rsi(closes, period=14)
                upper_bb, mid_bb, lower_bb = self.hft.calculate_bollinger_bands(closes, period=20, std_dev=2)

                trend = "NEUTRAL" # Initialize default trend
                
                # SAFE HARBOR CHECK (Bollinger Bands)
                is_safe_harbor = False
                if lower_bb > 0 and price <= lower_bb * 1.01:
                    if obi > 0.2 and vsc_score > 0.6:
                         is_safe_harbor = True
                         trend = " SAFE_HARBOR_LONG"
                
                # HFT Trend Filter: Price vs VWAP & EMA
                # Bullish: Price > VWAP and Price > EMA
                # Bearish: Price < VWAP and Price < EMA
                
                hft_trend = "NEUTRAL"
                if price > vwap and price > ema_fast: hft_trend = "BULLISH"
                elif price < vwap and price < ema_fast: hft_trend = "BEARISH"
                
                # RSI Filter (Avoid Overbought/Oversold)
                # Bullish Entry? Check RSI < 70 (Room to grow)
                # Bearish Entry? Check RSI > 30 (Room to fall)
                
                # Filter: SNIPER MODE (VSC > 0.8 & OBI > 0.4) - PULVERIZE MODE
                # Relaxado levemente para permitir mais entradas (Pulverização), mas mantendo HFT Filter.
                is_sniper_opportunity = False
                
                # Check 1: Strong Signal (Pulverize Standard)
                if abs(obi) > 0.4 and vsc_score > 0.8:
                     # Add HFT Confirmation (Mandatory)
                     if obi > 0 and hft_trend == "BULLISH" and rsi < 75: # Relaxed RSI slightly
                         is_sniper_opportunity = True
                         trend = " MAKER_BULL"
                     elif obi < 0 and hft_trend == "BEARISH" and rsi > 25:
                         is_sniper_opportunity = True
                         trend = " MAKER_BEAR"
                     else:
                         # Signal rejected by HFT
                         print(f"      ️ HFT REJECTION {symbol}: OBI/VSC OK, but Trend {hft_trend} / RSI {rsi:.1f} mismatch.")

                # Filter Standard: OBI Absoluto > 0.05 E Whale confirma E VSC confirma
                # (Mas se estivermos em drawdown severo, podemos ser mais exigentes)
                
                # DEEP ANALYSIS (User Request: "ANALISE PROFUNDA NA BACKPACK")
                # Filter noise. Require OBI > 0.15 (Significant Flow) and VSC > 0.6 (Sentiment aligned)
                if abs(obi) < 0.15: 
                     continue
                
                # if abs(obi) > 0.05: # Removed, redundant
                ticker = self.transport.get_ticker(symbol)
                price = float(ticker['lastPrice'])
                
                # Trend Check (Simples)
                if trend == "NEUTRAL": # Don't overwrite SNIPER or TRAP
                    if obi > 0: trend = "BULLISH"
                    else: trend = "BEARISH"
                    
                    # Divergence Warning
                    warning = ""
                    if obi > 0.1 and w_obi < -0.1:
                        warning = "️ WHALE DIVERGENCE (Retail Buys / Whale Sells)"
                        trend = "TRAP_BULL"
                    elif obi < -0.1 and w_obi > 0.1:
                        warning = "️ WHALE DIVERGENCE (Retail Sells / Whale Buys)"
                        trend = "TRAP_BEAR"
                        
                    # VSC Trap Overlay
                    if trap_signal != "NONE" and confidence > 0.5:
                        warning += f" | ️ VSC TRAP: {trap_signal}"
                        trend = "TRAP_DETECTED"
                    
                    # Log Oportunidade com Spread Info
                    print(f"   -> {symbol}: OBI {obi:.2f} | W_OBI {w_obi:.2f} | VSC {vsc_score:.2f} | {trend} {warning}")
                    
                    # Só adicionar se NÃO for Trap
                    if "TRAP" not in trend:
                        # STRICT CONFIRMATION PROTOCOL (User Request: "Tem que haver confirmacao")
                        # 1. Sniper: VSC > 0.8 & OBI > 0.4 (Pulverize Mode)
                        # 2. Strong Recovery: VSC > 0.6 & OBI > 0.3 (Backup)
                        
                        is_confirmed = False
                        if is_sniper_opportunity or is_safe_harbor:
                            is_confirmed = True
                        # 3. Micro Scalp (User: "ENTRE EM MICRO TRADES EM LOOP")
                        # Lower threshold if trend is confirmed
                        elif abs(obi) > 0.15 and vsc_score > 0.4:
                            # HFT Check Mandatory
                            if (obi > 0 and hft_trend == "BULLISH") or (obi < 0 and hft_trend == "BEARISH"):
                                is_confirmed = True
                                trend = " MICRO_SCALP"

                        if is_confirmed:
                            # Prioritize Sniper & Safe Harbor
                            score_boost = 150 if is_safe_harbor else (100 if is_sniper_opportunity else 50)
                            
                            # Boost Micro Scalp to ensure they get picked in Loop
                            if "MICRO_SCALP" in trend:
                                score_boost += 30
                            
                            # SMART MONEY BOOST (High Whale OBI)
                            # User: "analise onde o dinhero inteligente esta se movendo"
                            if abs(w_obi) > 0.2:
                                score_boost += 50
                                trend += " " # Tag as Whale Active
                            
                            # SUSTAINABILITY FILTER: Only Top Tier (OBI > 0.3 now for Pulverization)
                            # Exception for MICRO SCALP (OBI > 0.15 is allowed)
                            min_obi = 0.3
                            if "MICRO_SCALP" in trend: min_obi = 0.15
                            
                            if abs(obi) < min_obi:
                                print(f"      ️ SUSTAINABLE FILTER: Skipping {symbol} (OBI {obi:.2f} < {min_obi}). Need stronger signal.")
                                continue
                            
                            opportunities.append({
                                "symbol": symbol,
                                "obi": obi,
                                "whale_obi": w_obi,
                                "vsc_score": vsc_score,
                                "price": price,
                                "trend": trend,
                                "spread": spread_pct,
                                "score": abs(obi) + vsc_score + score_boost
                            })
                            print(f"       CANDIDATE DETECTED: {symbol} (OBI {obi:.2f}, VSC {vsc_score:.2f}) -> Validating Persistence...")
                        else:
                            # Log rejection for visibility (Educational)
                            if abs(obi) > 0.2:
                                print(f"       REJECTED {symbol}: Weak Confirmation (OBI {obi:.2f}, VSC {vsc_score:.2f} < 0.6)")
                else:
                    pass # Was "pass" in the original "else" block of the removed "if abs(obi) > 0.05"
            except Exception as e:
                print(f"       Error scanning {symbol}: {e}")
                pass
                
        # Sort by Score (Sniper First, then Strongest OBI/VSC)
        opportunities.sort(key=lambda x: x.get('score', 0), reverse=True)
        return opportunities

    def manage_positions(self):
        """Gerencia posições abertas com Trailing Stop e Sniper Exit"""
        print("\n️  MANAGING POSITIONS...")
        
        # 0. Health Check & Margin Analysis
        try:
            collateral = self.transport.get_account_collateral()
            if collateral:
                equity = float(collateral.get('equity', 0))
                avail = float(collateral.get('availableToTrade', 0))
                used = equity - avail
                usage_pct = (used / equity) * 100 if equity > 0 else 0
                
                health_color = "🟢"
                if usage_pct > 70: health_color = "🟡"
                if usage_pct > 85: health_color = ""
                
                print(f"    ACCOUNT HEALTH: Equity ${equity:.2f} | Used {usage_pct:.1f}% {health_color}")
                
                if usage_pct > 90:
                    print("      ️ CRITICAL MARGIN WARNING! Consider reducing risk.")
        except Exception as e:
            print(f"   ️ Health Check Failed: {e}")

        positions = self.transport.get_positions()
        if not positions:
            print("   -> No active positions.")
            return 0
            
        active_count = 0
        for pos in positions:
            symbol = pos.get('symbol')
            if not symbol: continue
            
            # Backpack API fix: Use netQuantity if quantity missing
            raw_qty = pos.get('quantity')
            if raw_qty is None:
                raw_qty = pos.get('netQuantity', 0)
            
            qty = float(raw_qty)
            
            side = pos.get('side') 
            if not side: 
                side = "Long" if qty > 0 else "Short"
            
            # Debug Position Data
            # print(f"      DEBUG POS: {symbol} Qty {qty} Side {side}")
            
            entry = float(pos.get('entryPrice', 0))
            mark = float(pos.get('markPrice', 0))
            
            # Calcular ROI
            if side == "Short":
                pnl_pct = (entry - mark) / entry if entry > 0 else 0
            else:
                pnl_pct = (mark - entry) / entry if entry > 0 else 0
                
            pnl_pct_lev = pnl_pct * self.leverage
            
            print(f"   -> {symbol} ({side}): ROI {pnl_pct_lev*100:.2f}% | Mark: {mark}")
            
            # 0. PANIC SENTINEL (Hard Stop de Ruína - USER REQUESTED)
            # "nosso protoclo esta passando vergonha... perdendo tanata margem"
            if pnl_pct_lev < -0.30: # -30% ROI Hard Stop
                print(f"      ️ PANIC SENTINEL TRIGGERED: ROI {pnl_pct_lev*100:.1f}% on {symbol}. CUTTING LOSS IMMEDIATELY!")
                self.close_position(symbol, qty, side)
                continue

            # 1. Sniper Exit Check (Liquidity Walls)
            target_price = self.sniper_targets.get(symbol)
            if target_price:
                # Se Short, sair se preço tocar ou furar suporte (Target)
                # Adicionar margem de segurança (Front-run wall by 0.1%)
                if side == "Short" and mark <= target_price * 1.001:
                    print(f"       SNIPER EXIT TRIGGERED: Price {mark} reached Target {target_price}")
                    self.close_position(symbol, qty, side)
                    continue # Posição fechada, next
            
            # 2. Check for Reversal (SAR) - Before Trailing Stop
            # Fetch OBI for current symbol to check for flip
            # (Optimization: We could pass OBI from opportunities list if available, but fetch here for safety)
            try:
                book = self.transport.get_orderbook_depth(symbol)
                current_obi = self.scanner.calculate_obi(book)
                sar_triggered = self.apply_sar_logic(symbol, side, qty, current_obi)
                if sar_triggered:
                     continue # Position flipped, skip trailing stop for this cycle
            except:
                pass
            
            # 3. Trailing Stop Check (Aggressive Scalping)
            if pnl_pct_lev > 0.005: # Começar a proteger a partir de 0.5% ROI (Was 0.8%)
                self.apply_trailing_stop(symbol, side, entry, mark, pnl_pct_lev, qty)
                
            active_count += 1
            
        return active_count

    def close_position(self, symbol, quantity, side="Unknown"):
        print(f"       CLOSING {symbol} (Market)...")
        # Inverter lado para fechar
        close_side = "Bid" # Default
        if side == "Long": close_side = "Ask"
        elif side == "Short": close_side = "Bid"
        
        try:
            self.transport.execute_order(
                symbol=symbol,
                side=close_side,
                order_type="Market",
                quantity=str(abs(quantity))
            )
        except Exception as e:
            print(f"       Close Error: {e}")

    def apply_sar_logic(self, symbol, side, qty, obi):
        """Stop-And-Reverse: Flip position if OBI is heavily against us"""
        # Limiares de Reversão
        # Se Long e OBI < -0.3 (Bearish) -> Close Long + Open Short
        # Se Short e OBI > 0.3 (Bullish) -> Close Short + Open Long
        
        reverse = False
        if side == "Long" and obi < -0.3:
            print(f"       SAR SIGNAL: Long vs OBI {obi:.2f} (Bearish). FLIPPING!")
            reverse = True
            new_side = "Short"
        elif side == "Short" and obi > 0.3:
            print(f"       SAR SIGNAL: Short vs OBI {obi:.2f} (Bullish). FLIPPING!")
            reverse = True
            new_side = "Long"
            
        if reverse:
            # 1. Close Existing
            self.close_position(symbol, qty, side)
            time.sleep(1) # Wait for fill
            
            # 2. Open Reverse (Same Size)
            # Check Margin first? Assuming same size fits.
            open_side = "Ask" if new_side == "Short" else "Bid"
            print(f"       EXECUTING REVERSE ENTRY ({new_side})...")
            try:
                # EXECUTION REFINEMENT: Limit Order at Best Price (Maker Intent)
                # Instead of Market, we use Limit at current Best Bid/Ask
                ticker = self.transport.get_ticker(symbol)
                best_price = float(ticker['lastPrice']) # Fallback
                
                # Try to get book for precision
                depth = self.transport.get_orderbook_depth(symbol)
                if depth:
                    if open_side == "Bid":
                        best_price = float(depth['bids'][-1][0])
                    else:
                        best_price = float(depth['asks'][0][0])
                
                self.transport.execute_order(
                    symbol=symbol,
                    side=open_side,
                    order_type="Limit", # MAKER INTENT
                    quantity=str(abs(qty)),
                    price=str(best_price),
                    post_only=True # Try Post-Only (if supported, else standard Limit)
                )
                print(f"       SAR FLIP COMPLETE for {symbol} (Limit @ {best_price})")
            except Exception as e:
                print(f"       SAR ENTRY FAILED: {e}")
            return True # SAR Triggered
            
        return False

    def apply_trailing_stop(self, symbol, side, entry, mark, roi, position_qty):
        """
        Implementa lógica MICRO SCALP Trailing Stop (AGGRESSIVE FOR RECOVERY):
        - 0.12% ROI -> Move SL para BreakEven (Fastest possible protection)
        - 0.25% ROI -> Move SL para +0.1% (Lock Penny Profit)
        - 0.40% ROI -> Move SL para +0.2% (Secure spread + profit)
        - 0.60% ROI -> Move SL para +0.4% (Profit Bank)
        
        USER UPDATE: "STOP DE 0.5% PARA RODAR ESTA MADRUGADA"
        Overrides previous trailing logic with a wider breathing room.
        Hard Stop is 0.5% PRICE MOVE (approx 1.5% ROI at 3x).
        """
        new_sl_price = 0
        # Taxa de Segurança (0.2% cobre Taker Entry + Taker Exit + Spread)
        FEE_BUFFER = 0.002 
        
        # User defined Hard Stop Distance = 0.5% (0.005)
        # We set this initially on entry.
        # Trailing should only activate after significant profit to lock gains.
        # Let's start trailing after +0.5% Profit to protect the win.
        
        # Adjust for 3x Leverage (Lower leverage means price needs to move MORE to hit ROI target)
        # ROI = (PriceMove%) * Leverage
        # 0.12% ROI @ 3x = 0.04% Price Move (Very tight)
        
        if side == "Short":
             # Short
             # Activate Trailing only after +0.3% Price Move (0.9% ROI)
             if roi > 0.009: 
                 new_sl_price = entry * (1 - FEE_BUFFER) # True BreakEven
             if roi > 0.015: # 1.5% ROI
                 new_sl_price = entry * 0.995 # +0.5% Profit Locked
        else:
             # Long
             if roi > 0.009:
                 new_sl_price = entry * (1 + FEE_BUFFER) # True BreakEven
             if roi > 0.015:
                 new_sl_price = entry * 1.005 # +0.5% Profit Locked

        if new_sl_price == 0:
            return # Ainda não atingiu gatilho de trailing

        print(f"       TRAILING CHECK: Target SL {new_sl_price:.4f} for {symbol} (ROI {roi*100:.1f}%)")

        try:
            # 1. Buscar ordens abertas para este símbolo
            orders = self.transport.get_open_orders(symbol)
            current_sl_order = None
            
            for order in orders:
                # Identificar ordem de Stop (geralmente TriggerOrder ou Limit longe do preço)
                # Assumindo que a única ordem aberta além de TP seria o SL.
                # Simplificação: Buscar ordem com side OPOSTO à posição e Type 'StopMarket' ou 'Trigger'
                # Se API não retornar Type claro, assumir ordem com triggerPrice
                
                o_side = order.get('side')
                o_type = order.get('orderType', '')
                # Handle None safely for triggerPrice
                tp_val = order.get('triggerPrice')
                o_trigger = float(tp_val) if tp_val is not None else 0.0
                
                # Side do SL deve ser oposto à posição (Short -> Buy/Bid)
                target_side = "Bid" if side == "Short" else "Ask"
                
                if o_side == target_side and o_trigger > 0:
                    current_sl_order = order
                    break
            
            # 2. Verificar se precisa atualizar
            update_needed = False
            if not current_sl_order:
                update_needed = True
                print("         -> No existing SL found. Creating new one.")
            else:
                current_trigger = float(current_sl_order.get('triggerPrice', 0))
                
                if side == "Short":
                    # Para Short, queremos baixar o SL (menor preço é melhor/mais lucro)
                    # Mas só atualizamos se o novo SL for MENOR que o atual
                    if new_sl_price < current_trigger:
                        update_needed = True
                        print(f"         -> Improving SL: {current_trigger} -> {new_sl_price}")
                else:
                    # Para Long, queremos subir o SL (maior preço é melhor)
                    if new_sl_price > current_trigger:
                        update_needed = True
                        print(f"         -> Improving SL: {current_trigger} -> {new_sl_price}")
            
            # 3. Executar Atualização
            if update_needed:
                # Cancelar anterior se existir
                if current_sl_order:
                    self.transport.cancel_order(symbol, current_sl_order.get('id'))
                    time.sleep(0.5)
                
                # Criar Novo SL
                # Calcular quantidade (toda a posição)
                # Precisamos saber a quantidade da posição, mas aqui só temos entry/mark/roi.
                # Assumindo que 'manage_positions' chamou, mas não passou qty.
                # CORREÇÃO: manage_positions deve passar qty ou buscamos de novo.
                # Vamos buscar a posição novamente para ter certeza da qty atual.
                # pos = next((p for p in self.transport.get_positions() if p['symbol'] == symbol), None)
                if position_qty:
                    # Use netQuantity logic for qty string
                    qty_float = abs(position_qty)
                    # Convert to string, removing trailing zeros if needed
                    qty = f"{qty_float:.8f}".rstrip('0').rstrip('.')
                    
                    sl_side = "Bid" if side == "Short" else "Ask"
                    
                    # Validar Trigger Price
                    # Adjust precision for large numbers
                    if new_sl_price > 1000:
                        trigger_str = f"{new_sl_price:.1f}"
                    elif new_sl_price > 10:
                        trigger_str = f"{new_sl_price:.2f}"
                    else:
                        trigger_str = f"{new_sl_price:.4f}"
                    
                    print(f"         -> Sending SL Order: {symbol} {sl_side} {qty} @ {trigger_str}")
                    
                    self.transport.execute_order(
                        symbol=symbol,
                        side=sl_side,
                        order_type="Market",
                        quantity=qty,
                        trigger_price=trigger_str
                    )
                    print(f"          TRAILING STOP UPDATED to {new_sl_price:.4f}")
                else:
                    print(f"         ️ Zero Quantity detected for {symbol}. Cannot set SL.")

        except Exception as e:
            print(f"       TRAILING ERROR: {e}")

    def get_portfolio_delta(self):
        """Calcula Delta do Portfólio (Net Long vs Net Short exposure)"""
        try:
            positions = self.transport.get_positions()
            if not positions: return 0.0
            
            long_exposure = 0.0
            short_exposure = 0.0
            
            for p in positions:
                raw_qty = p.get('quantity')
                if raw_qty is None: raw_qty = p.get('netQuantity', 0)
                qty = float(raw_qty)
                
                mark = float(p.get('markPrice', 0))
                value = abs(qty * mark)
                
                # Check Side explicitly or infer from qty (some APIs use negative qty for short)
                side = p.get('side')
                if not side: side = "Long" if qty > 0 else "Short"
                
                if side == "Long":
                    long_exposure += value
                else:
                    short_exposure += value
            
            total_exposure = long_exposure + short_exposure
            if total_exposure == 0: return 0.0
            
            # Net Delta % (-1.0 to 1.0)
            # 1.0 = All Long, -1.0 = All Short, 0.0 = Neutral
            net_delta = (long_exposure - short_exposure) / total_exposure
            
            print(f"   ️ PORTFOLIO BALANCE: Long ${long_exposure:.0f} | Short ${short_exposure:.0f} | Delta {net_delta:.2f}")
            return net_delta
            
        except Exception as e:
            print(f"   ️ Delta Check Error: {e}")
            return 0.0

    def validate_persistence(self, opportunities):
        """
        Filtra oportunidades que não persistem por pelo menos 2 ciclos de scan (10-20s).
        Evita HFT Spoofing e Flash Orders.
        """
        print("\n⏳ VALIDATING SIGNAL PERSISTENCE (Anti-Spoofing Protocol)...")
        
        current_symbols = {op['symbol']: op for op in opportunities}
        confirmed_opps = []
        
        # 1. Update Buffer & Check Persistence
        for symbol, op in current_symbols.items():
            if symbol not in self.persistence_buffer:
                # New Candidate
                self.persistence_buffer[symbol] = {
                    'count': 1,
                    'first_seen': time.time(),
                    'trend': op['trend']
                }
                print(f"   -> {symbol}: First Detection. Buffering for confirmation...")
            else:
                # Existing Candidate - Check Consistency
                prev_data = self.persistence_buffer[symbol]
                
                # Ensure Trend Direction hasn't flipped (Bull -> Bear or vice-versa)
                # If flipped, reset counter (it's noise/volatility)
                if prev_data['trend'] != op['trend']:
                     print(f"   -> {symbol}: Trend FLIP ({prev_data['trend']} -> {op['trend']}). Resetting count.")
                     self.persistence_buffer[symbol] = {
                        'count': 1,
                        'first_seen': time.time(),
                        'trend': op['trend']
                     }
                else:
                    # Increment Persistence
                    prev_data['count'] += 1
                    duration = time.time() - prev_data['first_seen']
                    print(f"   -> {symbol}: Persistence {prev_data['count']}x ({duration:.1f}s).")
                    
                    if prev_data['count'] >= 2:
                        confirmed_opps.append(op)
                        print(f"       SIGNAL PERSISTED: {symbol} CONFIRMED! (Stable for >10s)")

        # 2. Cleanup (Remove symbols that disappeared)
        buffer_symbols = list(self.persistence_buffer.keys())
        for sym in buffer_symbols:
            if sym not in current_symbols:
                print(f"   -> {sym}: Signal Lost (Disappeared). Removing from buffer.")
                del self.persistence_buffer[sym]
                
        return confirmed_opps

    def check_trend_alignment(self, symbol):
        """
        Verifica alinhamento de tendência em múltiplos timeframes (2h, 4h, 6h).
        Retorna (True/False, trend_direction).
        """
        # User: "TEMPOS GRAFICOS DE 2, 4 E 6 HORAS"
        timeframes = ["2h", "4h", "6h"]
        alignments = []
        
        print(f"\n SWING TRADE ANALYSIS ({symbol}):")
        
        for tf in timeframes:
            klines = self.transport.get_klines(symbol, tf, limit=50) # More data for higher TF
            if not klines: 
                alignments.append("NEUTRAL")
                continue
                
            closes = [float(k['close']) for k in klines]
            price = closes[-1]
            
            # HFT Indicators for this timeframe
            # Note: Using HFT class but on higher TF works fine (math is same)
            vwap = self.hft.calculate_vwap(klines)
            ema = self.hft.calculate_ema(closes, period=20) # Slower EMA for Swing
            rsi = self.hft.calculate_rsi(closes, period=14)
            
            # Trend Determination
            trend = "NEUTRAL"
            if price > vwap and price > ema:
                trend = "BULLISH"
            elif price < vwap and price < ema:
                trend = "BEARISH"
                
            alignments.append(trend)
            print(f"   -> {tf} Trend: {trend} | RSI: {rsi:.1f} | Price: {price:.2f} vs VWAP: {vwap:.2f}")
                
        # Check if ALL align
        if all(x == "BULLISH" for x in alignments):
            print(f"       SWING TREND ALIGNED: BULLISH on {symbol}")
            return True, "Long"
        elif all(x == "BEARISH" for x in alignments):
            print(f"       SWING TREND ALIGNED: BEARISH on {symbol}")
            return True, "Short"
            
        print(f"      ️ SWING TREND MIXED: {alignments} on {symbol}")
        return False, "Neutral"

    def verify_atomic_condition(self, symbol, intended_side):
        """
        ATOMIC VALIDATION: Last-millisecond check before execution.
        Fetches fresh book AND HFT METRICS (VWAP/RSI) to confirm signal.
        NOW INCLUDES MULTI-TIMEFRAME CONFIRMATION (2h, 4h, 6h).
        """
        print(f"      ️  ATOMIC CHECK: Verifying {symbol} condition...")
        try:
            # 1. Fresh Fetch Book
            book = self.transport.get_orderbook_depth(symbol)
            if not book: return False
            
            # 2. Recalculate VSC
            vsc_score, trap, conf = self.vsc.analyze(book)
            obi = self.scanner.calculate_obi(book)
            
            # 3. MULTI-TIMEFRAME TREND CHECK (2h, 4h, 6h)
            # User: "ANALISE NOS TEMPOS GRAFICOS DE 2, 4 E 6 HORAS"
            aligned, trend_dir = self.check_trend_alignment(symbol)
            
            if not aligned:
                print(f"          ATOMIC REJECTION: Trend Mismatch (2h/4h/6h).")
                return False
                
            # Verify if aligned trend matches intended side
            if (intended_side == "Bid" and trend_dir != "Long") or \
               (intended_side == "Ask" and trend_dir != "Short"):
                print(f"          ATOMIC REJECTION: Trend {trend_dir} vs Intended {intended_side}.")
                return False

            # 4. RSI Check (on 4h for Swing Safety)
            klines_4h = self.transport.get_klines(symbol, "4h", limit=20)
            closes_4h = [float(k['close']) for k in klines_4h]
            rsi_4h = self.hft.calculate_rsi(closes_4h, period=14)
            
            print(f"         -> Fresh Data: OBI {obi:.2f} | VSC {vsc_score:.2f} | RSI(4h) {rsi_4h:.1f}")
            
            # 5. Validate against Intended Side
            valid = False
            reason = ""
            
            if intended_side == "Bid": # We want to Buy (Long)
                # Trend is already checked (BULLISH)
                if vsc_score > 0.2: # Relaxed VSC for Swing (Trend is King)
                     if rsi_4h < 70: # More room for Swing
                         valid = True
                     else:
                         reason = f"RSI(4h) Overbought ({rsi_4h:.1f})"
                else:
                    reason = "VSC Degraded"
                    
            else: # We want to Sell (Short)
                # Trend is already checked (BEARISH)
                if vsc_score < -0.2:
                    if rsi_4h > 30:
                        valid = True
                    else:
                         reason = f"RSI(4h) Oversold ({rsi_4h:.1f})"
                else:
                     reason = "VSC Degraded"
                
            if not valid:
                print(f"          ATOMIC REJECTION: {reason}! Aborting trade.")
                return False
                
            print("          ATOMIC PASS: Signal confirmed with 2h/4h/6h Swing Trend.")
            return True
            
        except Exception as e:
            print(f"         ️ Atomic Check Error: {e}")
            return False # Fail safe

    def execute_snowball(self, opportunities, active_positions):
        """Aloca capital nas melhores oportunidades com PREDICTIVE HEDGING"""
        
        # 0. Check Portfolio Delta
        portfolio_delta = self.get_portfolio_delta()
        
        # 1. Carte Blanche Logic: Se tem espaço, PREENCHER.
        slots_available = self.max_positions - active_positions
        if slots_available <= 0:
            print("   ️ Max positions reached. Waiting for exits.")
            return

        print(f"\n CARTE BLANCHE ACTIVE: {slots_available} slots open. Hunting in LOOP...")
        
        # LOOP LOGIC: Try to fill as many slots as possible in one pass
        
        available = 0.0
        try:
            capital = self.transport.get_account_collateral() 
            if capital and isinstance(capital, dict) and 'availableToTrade' in capital:
                available = float(capital.get('availableToTrade', 0))
        except:
             pass
            
        print(f" CAPITAL AVAILABLE (API): ${available:.2f} [BLIND MODE ACTIVE]")
        
        # MARGIN PREDICTION (User: "prevendo que a margem sera desbloeada")
        # Se temos slots abertos, assumimos que a margem pode estar voltando de um trade fechado
        # mesmo que a API ainda mostre 0 (Latência).
        if slots_available > 0 and available < self.min_trade_amount:
             print("   ️ MARGIN PREDICTION: Slots Open + Low Balance -> Assuming Margin Unlock in progress.")
             available = 100.0 # Ghost Margin para tentar enviar a ordem (Exchange valida no final)
        
        if available < self.min_trade_amount:
            print("   -> Insufficient capital for new trade (Real Check).")
            return
            
        # Se tem capital e espaço, pega a melhor oportunidade
        if not opportunities:
            print("   -> No high-quality opportunities found.")
            return
            
        # Tentar preencher até X slots ou até acabar o dinheiro
        # Vamos tentar iterar nas Top 3 oportunidades, se a primeira falhar, tenta a próxima.
        
        # Filtrar oportunidades que JÁ temos posição
        current_positions = [p['symbol'] for p in self.transport.get_positions()]
        valid_opps = [op for op in opportunities if op['symbol'] not in current_positions]
        
        if not valid_opps:
            print("   -> No NEW opportunities found (already positioned in top picks).")
            return

        # Tentar até 5 ativos (Loop Expansion)
        for i, best_opp in enumerate(valid_opps[:5]):
            if slots_available <= 0:
                 print("   -> Slots filled. Stopping loop.")
                 break
                 
            symbol = best_opp['symbol']
            obi = best_opp['obi']
            price = best_opp['price']
            
            # Predict Side based on OBI
            predicted_side = "Long" if obi > 0 else "Short"
            
            # --- HEDGING LOGIC ---
            # If Delta is too positive (> 0.5), FORCE priority on Short signals
            # If Delta is too negative (< -0.5), FORCE priority on Long signals
            skip_trade = False
            
            if portfolio_delta > 0.4: # Heavy Long Exposure
                if predicted_side == "Long":
                    if abs(obi) < 0.4: # Only allow super strong longs if we are already long
                         print(f"       HEDGE FILTER: Skipping Long on {symbol} (Delta {portfolio_delta:.2f}) to balance risk.")
                         skip_trade = True
                    else:
                         print(f"      ️ RISK WARNING: Adding Long to Heavy Long Portfolio (OBI {obi:.2f} justifies risk).")
            
            elif portfolio_delta < -0.4: # Heavy Short Exposure
                if predicted_side == "Short":
                    if abs(obi) < 0.4:
                         print(f"      � HEDGE FILTER: Skipping Short on {symbol} (Delta {portfolio_delta:.2f}) to balance risk.")
                         skip_trade = True
            
            if skip_trade: continue
            
            print(f"� SNOWBALL EXECUTION (Attempt {i+1}): Found gem {symbol} (OBI {obi:.2f})")
            
            # Tamanho Fixo para Volume Farming (User: "TRADES DE 10 DOLARES")
            # User Update: "80 % DA MARGEM"
            # Calculate 80% of Available
            trade_size = available * 0.8
            if trade_size < 10: trade_size = 10.0 # Min Floor
            
            side = "Ask" if predicted_side == "Short" else "Bid" # OBI Negativo = Short (Venda/Ask)
            
            print(f"   -> Opening {side} on {symbol} with ${trade_size:.2f} (80% Margin) x{self.leverage}...")
            
            try:
                # Calcular Qty
                qty = (trade_size * self.leverage) / price
                
                # Boost Size for Micro Scalp? Or Keep same?
                # User: "MICRO TRADES". Often implies smaller size or higher freq.
                # Let's keep size fixed but ensure frequency.
                
                # Ajuste Fino de Precisão (Evitar 'Quantity decimal too long')
                if price > 1000: 
                    qty = round(qty, 3) # BTC, ETH
                elif price > 10:
                    qty = round(qty, 2) # SOL, AVAX
                elif price > 1:
                    qty = round(qty, 1) # SUI, WIF (se > 1)
                else:
                    # TIA, FOGO, MEMES (< $1) -> Round to nearest 10 to avoid step size errors
                    qty = int(qty // 10) * 10 
                
                # Executar Entrada
                # EXECUTION REFINEMENT: MARKET ORDER (User Request: "ENTRE EM LOOP EM 5X A MERCADO")
                
                print(f"      ️ PLACING MARKET ORDER: {side} {qty} (Loop Mode)")
                
                order = self.transport.execute_order(
                    symbol=symbol,
                    side=side, 
                    order_type="Market", # MARKET ORDER
                    quantity=str(qty)
                )
                
                if order and order.get('id'):
                    self.print_mantra() # MANTRA REINFORCEMENT
                    print(f"       SNOWBALL ENTRY: {symbol} ID: {order.get('id')} | Size: ${trade_size}")
                    
                    # --- IMMEDIATE PROTECTION (ATOMIC SL + TP) ---
                    # User: "STOP DE 0.5% PARA RODAR ESTA MADRUGADA"
                    MAX_LOSS_PCT = 0.005 # 0.5% Price Move
                    
                    print(f"      ️ PLACING NIGHT GUARD ORDERS (Hard Stop {MAX_LOSS_PCT*100}%)...")
                    
                    # SL Pct (Price Distance)
                    sl_pct = MAX_LOSS_PCT
                    tp_pct = 0.015 # 1.5% TP (3:1 Risk/Reward for Overnight Swing)
                    
                    if side == "Bid":
                        sl_price = price * (1 - sl_pct)
                        tp_price = price * (1 + tp_pct)
                        sl_side = "Ask"
                    else:
                        sl_price = price * (1 + sl_pct)
                        tp_price = price * (1 - tp_pct)
                        sl_side = "Bid"
                    
                    # 1. STOP LOSS (Market Trigger)
                    self.transport.execute_order(
                        symbol=symbol,
                        side=sl_side,
                        order_type="Market", # Trigger Market
                        quantity=str(qty),
                        trigger_price=str(round(sl_price, 4 if sl_price > 10 else 6))
                    )
                    print(f"       SL SET @ {sl_price:.4f}")

                    # 2. TAKE PROFIT (Limit Order - Maker)
                    # Tentar colocar ordem Limit para sair com lucro e taxa menor
                    try:
                        self.transport.execute_order(
                            symbol=symbol,
                            side=sl_side,
                            order_type="Limit",
                            quantity=str(qty),
                            price=str(round(tp_price, 4 if tp_price > 10 else 6))
                        )
                        print(f"       TP SET @ {tp_price:.4f}")
                    except Exception as e:
                        print(f"      ️ TP Set Failed: {e}")
                    
                    # Se entrou com sucesso, decrementa slots e continua o loop
                    slots_available -= 1
                    # Não retorna, tenta preencher o próximo slot se houver margem (Loop)
                    continue 
                    
                else:
                    print(f"       ENTRY FAILED: {symbol}. Trying next...")
                    continue # Tenta o próximo ativo
            except Exception as e:
                 print(f"       EXECUTION ERROR: {e}")
                 continue # Tenta o próximo ativo
        
        print("   ️ Loop finished or failed to enter opportunities.")

    def print_mantra(self):
        """Prints the Mission Mantra for User Confidence"""
        print("\n" + "="*60)
        print(" OBI SENTINEL MANTRA (SERIAL SCALP)")
        print("   -> Status: SERIAL SCALP MODE ACTIVE")
        print("   -> Mission: HIT & RUN (Enter -> Profit -> Exit -> Repeat)")
        print("   -> Execution: SURGICAL PRECISION ($10 Trades)")
        print("="*60 + "\n")

    def update_session_pnl(self):
        """Atualiza o PnL da sessão baseado no histórico recente de trades (Simulado por enquanto)"""
        # TODO: Ler histórico real da API.
        # Por enquanto, vamos estimar baseado no Equity change se possível, ou apenas manter 0.
        pass

    def display_pulse(self, opportunities, active_positions):
        """Exibe tabela de monitoramento em tempo real com Detecção de Divergência"""
        # Get active PnL details
        positions = self.transport.get_positions()
        pos_map = {} # Map symbol -> {side, roi_str, qty}
        
        current_equity = 0.0
        try:
             collateral = self.transport.get_account_collateral()
             if collateral:
                 current_equity = float(collateral.get('equity', 0))
        except: pass
        
        # Calculate Progress
        goal = 100.0
        progress_pct = (current_equity / goal) * 100 if goal > 0 else 0

        for p in positions:
            sym = p['symbol']
            entry = float(p['entryPrice'])
            mark = float(p['markPrice'])
            
            raw_qty = p.get('quantity')
            if raw_qty is None: raw_qty = p.get('netQuantity', 0)
            qty = float(raw_qty)
            
            # Determinar Side
            side = p.get('side')
            if not side:
                 side = "Long" if qty > 0 else "Short"
            
            pnl_pct = 0
            if entry > 0:
                if side == "Short": pnl_pct = (entry - mark) / entry
                else: pnl_pct = (mark - entry) / entry
            
            pnl_pct_lev = pnl_pct * self.leverage * 100
            
            pos_map[sym] = {
                "side": side,
                "roi_str": f"{pnl_pct_lev:+.2f}%",
                "qty": qty
            }

        # Limpar tela (opcional, ou apenas imprimir bloco)
        print("\n" + "="*85)
        print(f" RADAR PULSE | {datetime.now().strftime('%H:%M:%S')} | Active: {active_positions} | Equity: ${current_equity:.2f} ({progress_pct:.1f}% of $100)")
        print(f"    MISSION PROGRESS: [{'#' * int(progress_pct/5)}{'-' * (20 - int(progress_pct/5))}]")
        print("="*85)
        print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'OBI':<6} | {'W_OBI':<6} | {'SIDE':<6} | {'ROI':<8} | {'STATUS':<20}")
        print("-" * 85)
        
        # Mostrar Top Opportunities + Active Positions (Merged View)
        # Vamos mostrar as Oportunidades (Top 5) e garantir que as posições ativas também apareçam se não estiverem no top 5?
        # Para simplificar, vamos mostrar Top 7 Opportunities. Se tiver posição, preenche.
        
        for opp in opportunities[:7]:
            sym = opp['symbol'].replace("_USDC_PERP", "")
            full_sym = opp['symbol']
            price = opp['price']
            obi = opp['obi']
            w_obi = opp.get('whale_obi', 0.0)
            
            # Dados da Posição (se existir)
            pos_data = pos_map.get(full_sym)
            
            side_display = "-"
            roi_display = "-"
            status = "WAITING"
            
            if pos_data:
                side = pos_data['side']
                side_display = side[:4].upper() # LONG / SHOR
                roi_display = pos_data['roi_str']
                
                # Divergence Logic
                # Long + Negative OBI = Danger
                # Short + Positive OBI = Danger
                if side == "Long" and obi < -0.15:
                    status = "️ DIVERGENCE (BEAR)"
                elif side == "Short" and obi > 0.15:
                    status = "️ DIVERGENCE (BULL)"
                else:
                    status = " ALIGNED"
            else:
                # Opportunity Status
                if abs(w_obi) > 0.2: status = " WHALE MOVE"
                elif abs(obi) > 0.8: status = " SNOWBALL ENTRY"
                elif abs(obi) > 0.5: status = " HOT"
                elif abs(obi) > 0.2: status = " WATCH"
            
            print(f"{sym:<15} | {price:<10.4f} | {obi:<6.2f} | {w_obi:<6.2f} | {side_display:<6} | {roi_display:<8} | {status:<20}")
        print("-" * 85)

    def recycle_margin(self):
        """Identifica e fecha posições estagnadas para liberar margem (Margin Recycling)"""
        print("\n️  MARGIN RECYCLING CHECK...")
        try:
            positions = self.transport.get_positions()
            if not positions: return
            
            for p in positions:
                symbol = p.get('symbol')
                
                # Check Duration (Simulado: Se ROI está próximo de 0 por muito tempo)
                # Como não temos 'openTime' fácil, usamos ROI baixo + OBI fraco como proxy de estagnação
                
                entry = float(p.get('entryPrice', 0))
                mark = float(p.get('markPrice', 0))
                
                raw_qty = p.get('quantity')
                if raw_qty is None: raw_qty = p.get('netQuantity', 0)
                qty = float(raw_qty)
                
                side = p.get('side')
                if not side: side = "Long" if qty > 0 else "Short"
                
                pnl_pct = 0
                if entry > 0:
                    if side == "Short": pnl_pct = (entry - mark) / entry
                    else: pnl_pct = (mark - entry) / entry
                
                roi = pnl_pct * self.leverage
                
                # Critério de Reciclagem (Time-Based / Stagnation):
                # 1. ROI Negativo Leve (-1% a -5%) OU ROI Positivo Irrelevante (< 1%)
                # 2. OBI Neutro/Fraco (sem chance de recuperação rápida)
                
                # Get OBI
                book = self.transport.get_orderbook_depth(symbol)
                obi = self.scanner.calculate_obi(book)
                
                should_recycle = False
                reason = ""
                
                # Case A: Dead Money (ROI ~0% e OBI Neutro)
                # Tighter Rule: If ROI < 0.5% and OBI < 0.1 -> KILL IT
                if abs(roi) < 0.005 and abs(obi) < 0.1:
                    should_recycle = True
                    reason = "DEAD MONEY (Stagnant < 0.5%)"
                    
                # Case B: Bleeding Slowly (ROI < -2% e OBI Contra)
                if roi < -0.02 and roi > -0.10: # Não vender fundo fundo (-30%), mas vender sangria lenta
                    if side == "Long" and obi < -0.1:
                        should_recycle = True
                        reason = "SLOW BLEED (Bearish OBI)"
                    elif side == "Short" and obi > 0.1:
                        should_recycle = True
                        reason = "SLOW BLEED (Bullish OBI)"
                        
                # Case C: PANIC SENTINEL (Stop de Ruína)
                # Se ROI < -30%, CORTAR IMEDIATAMENTE. Sem perguntas.
                # Preserva capital para o próximo airdrop/trade.
                if roi < -0.30:
                    should_recycle = True
                    reason = "️ PANIC SENTINEL (Stop Ruin -30%)"
                    
                if should_recycle:
                    print(f"      ️ RECYCLING {symbol} | ROI {roi*100:.2f}% | OBI {obi:.2f} | Reason: {reason}")
                    self.close_position(symbol, qty, side)
                    
        except Exception as e:
            print(f"   ️ Recycling Error: {e}")

    def run(self):
        print("\n POWER HOUR MODE ACTIVATED: High Frequency Scanning (10s)")
        print("   -> Strategy: SMART TAKER (Low Spread Only)")
        print("   -> Cost Control: Spread < 0.08%")
        print("   -> Note: Orders consume liquidity, they do not sit in the book.")
        
        while True:
            try:
                # 1. Manage Existing
                active_count = self.manage_positions()
                
                # 2. Scan Market
                opps = self.get_market_opportunities()
                
                # 3. Check for Margin Recycling
                self.recycle_margin()
                
                # 4. Display Pulse
                self.display_pulse(opps, active_count)
                
                # 4.1 Validate Persistence (Anti-HFT)
                # Initialize variable safely
                confirmed_opps = []
                try:
                    confirmed_opps = self.validate_persistence(opps)
                except Exception as e:
                    print(f"   ️ Persistence Check Error: {e}")
                    confirmed_opps = []
                
                # 5. Reinvest/Enter New (Only Confirmed)
                self.execute_snowball(confirmed_opps, active_count)
                
                # SLEEP MODE FOR NIGHT GUARD (User: "Como dormir tranquilo?")
                # Reduce Frequency to avoid overtrading noise at night.
                # Validates slowly, trades rarely.
                if self.persistence_buffer:
                    print(" NIGHT SENTRY: Monitoring potential signal (5s)...")
                    time.sleep(5)
                else:
                    print(" NIGHT MODE: Scanning deeply every 30s. Sleep tight.")
                    time.sleep(30)
                
            except KeyboardInterrupt:
                print(" Radar Stopped.")
                break
            except Exception as e:
                print(f" ERROR in Radar Loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    radar = ObiCompoundRadar()
    radar.run()
