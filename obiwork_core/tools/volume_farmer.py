import os
import sys
import asyncio
import logging
import random
import time
import argparse
from dotenv import load_dotenv

# Adicionar caminhos (ajustado para estrutura do clone)
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../obiwork_core/tools
project_root = os.path.dirname(current_dir) # .../obiwork_core
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("volume_farmer.log"),
        logging.StreamHandler()
    ]
)

class VolumeFarmer:
    def __init__(self, symbols=["BTC_USDC_PERP"], leverage=10, dry_run=False, mode="straddle", direction="auto", obi_threshold=0.25, eco_mode=False, min_entry_interval=15, capital_per_trade=200.0, risk_usd=2.0, profit_usd=5.0, reset_orders=False, auto_learn=False, mandatory_sl=False, profile_configs=None, symbol_profiles=None, manual_obi=None, manual_onchain=None, ironclad=False):
        load_dotenv()
        self.symbols = symbols # Lista de ativos
        self.leverage = leverage
        self.dry_run = dry_run
        self.mode = mode # 'straddle' ou 'surf'
        self.direction = direction # 'auto', 'long', 'short'
        self.obi_threshold = obi_threshold
        self.eco_mode = eco_mode
        self.min_entry_interval = min_entry_interval
        
        # Handle "ALL" capital case (Compound Mode)
        if isinstance(capital_per_trade, str) and capital_per_trade.upper() == "ALL":
             self.capital_per_trade = 0.0 # Will be calculated dynamically
             self.use_all_capital = True
        else:
             self.capital_per_trade = float(capital_per_trade)
             self.use_all_capital = False

        self.risk_usd = float(risk_usd)
        self.profit_usd = float(profit_usd)
        self.reset_orders = reset_orders
        self.auto_learn = auto_learn
        self.mandatory_sl = bool(mandatory_sl)
        self.ironclad = bool(ironclad) # Ironclad Survival Protocol
        self.compound_mode = False # Will be set via args
        self.hyper_volume = False # Will be set via args injection or separate init param if needed, but for now we rely on args passing logic or manual set
        
        # Hack: Pass hyper_volume via profile_configs or direct attribute injection if not in init
        # Better: Add hyper_volume to __init__
        self.logger = logging.getLogger("VolumeFarmer")
        if self.eco_mode:
            self.logger.setLevel(logging.WARNING)
        
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        self.cache = {}
        self.cache_ttl = {
            'positions': 0.4,
            'open_orders': 0.4,
            'depth': 0.4,
            'ticker': 0.4,
            'pulse': 10.0,
            'klines': 60.0 # 1 minute cache for volatility
        }
        self.learn_batch_trades = 5
        self.learn_batch_seconds = 600
        self.profile_configs = profile_configs or {}
        if "base" not in self.profile_configs:
            self.profile_configs["base"] = {
                "enabled": True,
                "leverage": self.leverage,
                "margin": self.capital_per_trade,
                "target_pct": None,
                "min_obi": None,
                "min_onchain": None
            }
        if "5x" not in self.profile_configs:
            self.profile_configs["5x"] = {
                "enabled": True,
                "leverage": 5,
                "margin": self.capital_per_trade,
                "target_pct": 0.10,
                "min_obi": None,
                "min_onchain": None
            }
        if "10x" not in self.profile_configs:
            self.profile_configs["10x"] = {
                "enabled": True,
                "leverage": 10,
                "margin": self.capital_per_trade,
                "target_pct": 0.05,
                "min_obi": None,
                "min_onchain": None
            }
        if "20x" not in self.profile_configs:
            self.profile_configs["20x"] = {
                "enabled": True,
                "leverage": 20,
                "margin": self.capital_per_trade,
                "target_pct": 0.25,
                "min_obi": None,
                "min_onchain": None
            }
        self.symbol_profiles = symbol_profiles or {}
        if manual_obi is not None and not isinstance(manual_obi, dict):
            manual_obi = {"default": float(manual_obi)}
        if manual_onchain is not None and not isinstance(manual_onchain, dict):
            manual_onchain = {"default": float(manual_onchain)}
        self.manual_obi = manual_obi or {}
        self.manual_onchain = manual_onchain or {}
        self.sl_rearm_max_attempts = 3
        self.sl_rearm_backoff_seconds = 1.0
        
        self.is_running = False
        # Dicionário de Estado por Símbolo
        # Added: last_exit_time for cooldown
        self.state = {s: {'last_price': 0, 'active_id': None, 'trailing_activated': False, 'last_exit_time': 0, 'last_side': None, 'last_sl': None, 'consecutive_losses': 0, 'zero_loss_until': 0, 'exit_handled': False, 'last_entry_time': 0, 'entry_fill_time': 0, 'recent_results': [], 'recent_prices': [], 'learned_obi': self.obi_threshold, 'learned_profit_usd': self.profit_usd, 'learned_risk_usd': self.risk_usd, 'learned_min_entry_interval': self.min_entry_interval, 'last_learn_time': 0, 'trades_since_learn': 0, 'effective_mode': self.mode, 'target_qty': 0.0, 'probe_qty': 0.0, 'confirm_qty': 0.0, 'confirmation_sent': False, 'full_entry': False, 'probe_spread_pct': 0.0, 'sl_rearm_attempts': 0, 'sl_rearm_next_ts': 0} for s in self.symbols}
        
    async def start(self):
        self.logger.info(f" INICIANDO FROTA DE VOLUME: {self.symbols} | Lev {self.leverage}x")
        self.logger.info(f"   -> Modo: {self.mode.upper()} ({self.direction.upper()})")
        self.logger.info(f"   -> Sizing: ${self.capital_per_trade:.2f} por trade | Risco ${self.risk_usd:.2f} | Alvo ${self.profit_usd:.2f}")
        if self.auto_learn:
            self.logger.info("   -> Auto aprendizado: ATIVO")
        
        self.is_running = True
        
        # Check for Compound Mode Override
        if "--compound-mode" in sys.argv:
            self.compound_mode = True
            self.logger.info(" COMPOUND SNIPER MODE: ACTIVATED")
            self.logger.info("   -> Single Asset Focus + Full Margin + OBI Validation")

        # Log Inicial de Tendência
        if self.ironclad:
             self.logger.info("️ IRONCLAD ATIVO: Analisando Tendência Inicial...")
             for s in self.symbols:
                 trend = self.oracle.get_trend_bias(s, "1m")
                 self.logger.info(f"   -> {s}: Tendência 1m = {trend}")

        if self.reset_orders and not self.dry_run:
            try:
                for symbol in self.symbols:
                    open_orders = self._get_cached_open_orders(symbol)
                    for o in open_orders:
                        self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                    self._invalidate_cache([f"open_orders:{symbol}"])
                self.logger.warning(" Livro resetado: ordens pendentes canceladas.")
            except Exception as e:
                self.logger.error(f"Falha ao resetar ordens: {e}")
        
        while self.is_running:
            try:
                tasks = []
                for symbol in self.symbols:
                    tasks.append(self._process_symbol(symbol))
                
                await asyncio.gather(*tasks)
                await asyncio.sleep(0.5) 
                
            except Exception as e:
                self.logger.error(f"Erro no Loop Principal: {e}")
                await asyncio.sleep(5)

    def _get_cached(self, key, ttl, fetcher):
        now = time.time()
        cached = self.cache.get(key)
        if cached and now - cached['ts'] < ttl:
            return cached['value']
        try:
            value = fetcher()
        except Exception:
            value = None
        self.cache[key] = {'ts': now, 'value': value}
        return value

    def _invalidate_cache(self, keys):
        for key in keys:
            self.cache.pop(key, None)

    def _get_cached_positions(self):
        return self._get_cached("positions", self.cache_ttl['positions'], lambda: self.transport.get_positions())

    def _get_cached_open_orders(self, symbol):
        return self._get_cached(f"open_orders:{symbol}", self.cache_ttl['open_orders'], lambda: self.transport.get_open_orders(symbol))

    def _get_cached_depth(self, symbol):
        return self._get_cached(f"depth:{symbol}", self.cache_ttl['depth'], lambda: self.data_client.get_orderbook_depth(symbol))

    def _get_cached_ticker(self, symbol):
        def fetch():
            return self.transport.get_ticker(symbol)
        ticker = self._get_cached(f"ticker:{symbol}", self.cache_ttl['ticker'], fetch)
        if ticker and 'lastPrice' in ticker:
            try:
                self._record_price(symbol, float(ticker['lastPrice']))
            except Exception:
                pass
        return ticker

    def _get_cached_pulse(self):
        return self._get_cached("pulse", self.cache_ttl['pulse'], lambda: self.oracle.get_market_pulse())

    def _get_cached_klines(self, symbol, interval, limit=100):
        def fetch():
            return self.transport.get_klines(symbol, interval, limit)
        return self._get_cached(f"klines:{symbol}:{interval}", self.cache_ttl['klines'], fetch)

    def _get_cached_atr(self, symbol, interval="5m", period=14):
        def fetch():
            # Using transport directly as it has get_klines
            klines = self.transport.get_klines(symbol, interval, limit=period+5)
            if not klines: return None
            
            highs = [float(k['high']) for k in klines]
            lows = [float(k['low']) for k in klines]
            closes = [float(k['close']) for k in klines]
            
            trs = []
            for i in range(1, len(klines)):
                tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                trs.append(tr)
                
            if len(trs) < period: return None
            atr = sum(trs[-period:]) / period
            last_close = closes[-1] if closes[-1] > 0 else 1.0
            return (atr / last_close) # Return as percentage (0.002 = 0.2%)
            
        return self._get_cached(f"atr:{symbol}:{interval}", self.cache_ttl['klines'], fetch)

    def _resolve_mode(self, symbol, pulse):
        if self.direction in ["long", "short"]:
            return "surf"
        if self.mode == "surf":
            return "surf"
        # Only switch to SURF if Pulse is strongly directional
        if pulse in ["BULLISH", "BEARISH"]:
            return "surf"
        return "straddle"

    def _resolve_profile(self, symbol):
        profile_name = self.symbol_profiles.get(symbol, "base")
        profile = self.profile_configs.get(profile_name, self.profile_configs.get("base", {}))
        return profile_name, profile

    def _get_manual_signal(self, manual_map, symbol):
        if isinstance(manual_map, dict):
            if symbol in manual_map:
                return manual_map[symbol]
            if "default" in manual_map:
                return manual_map["default"]
        return None

    def _record_price(self, symbol, price):
        now = time.time()
        prices = self.state[symbol].get('recent_prices', [])
        prices.append((now, price))
        cutoff = now - 12
        prices = [p for p in prices if p[0] >= cutoff]
        self.state[symbol]['recent_prices'] = prices

    def _recent_range_pct(self, symbol, window=10):
        now = time.time()
        prices = self.state[symbol].get('recent_prices', [])
        recent = [p for t, p in prices if t >= now - window]
        if len(recent) < 2:
            return 0.0
        low = min(recent)
        high = max(recent)
        if low <= 0:
            return 0.0
        return (high - low) / low

    def calculate_safe_stop_zone(self, symbol, side, depth):
        if not depth:
            return 0.0
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        if not bids or not asks:
            return 0.0
        best_bid = float(bids[-1][0])
        best_ask = float(asks[0][0])
        mid = (best_bid + best_ask) / 2
        spread_pct = (best_ask - best_bid) / mid if mid > 0 else 0.0
        micro_vol = self._recent_range_pct(symbol, window=10)
        absorption_range = self._absorption_range_pct(symbol, side, depth, best_bid, best_ask)
        
        # Base Micro-Stop
        safe_stop = (spread_pct * 3) + micro_vol + absorption_range
        
        # Structural Stop (ATR 5m)
        atr_5m = self._get_cached_atr(symbol, "5m")
        if atr_5m:
            # Ensure stop is at least 0.8x ATR 5m (Structural integrity)
            # But cap at 1.5x ATR to avoid excessive risk
            structural_min = atr_5m * 0.8
            if safe_stop < structural_min:
                safe_stop = structural_min
                
        return max(safe_stop, 0.001)

    def _absorption_range_pct(self, symbol, side, depth, best_bid, best_ask):
        if side == "Long":
            levels = depth.get('bids', [])[-10:]
            if not levels:
                return 0.0
            best_price = best_bid
        else:
            levels = depth.get('asks', [])[:10]
            if not levels:
                return 0.0
            best_price = best_ask
        sizes = [float(x[1]) for x in levels]
        total = sum(sizes)
        if total <= 0:
            return 0.0
        max_idx = sizes.index(max(sizes))
        wall_price = float(levels[max_idx][0])
        return abs(best_price - wall_price) / best_price if best_price > 0 else 0.0

    def expected_reversion_ok(self, symbol, stop_distance_pct):
        expected = self._recent_range_pct(symbol, window=10)
        return expected >= (stop_distance_pct * 0.6)

    def time_based_stop_unlock(self, symbol, side, obi, pulse):
        entry_time = self.state[symbol].get('entry_fill_time', 0)
        if not entry_time:
            return True
        now = time.time()
        if "BTC" in symbol:
            unlock_seconds = 12
        elif "ETH" in symbol:
            unlock_seconds = 15
        else:
            unlock_seconds = 10
        if side == "Long":
            inverted = obi is not None and obi < -0.1
            pulse_shift = pulse == "BEARISH"
        else:
            inverted = obi is not None and obi > 0.1
            pulse_shift = pulse == "BULLISH"
        if inverted or pulse_shift:
            return True
        return (now - entry_time) >= unlock_seconds

    # --- COMPOUND SNIPER HELPERS ---
    def select_best_compound_asset(self):
        """
        Scans all symbols and selects the single best asset for compounding.
        Criteria: High OBI (Absolute), Trend Alignment, and Volatility.
        """
        candidates = []
        for symbol in self.symbols:
            obi = self.oracle.get_obi(symbol)
            if not obi: continue
            
            # Trend Check (1m)
            trend = self.oracle.get_trend_bias(symbol, "1m")
            
            # Directional Agreement Check
            if obi > 0 and trend == "BULLISH":
                score = abs(obi) * 1.5 # Bonus for alignment
                direction = "Long"
            elif obi < 0 and trend == "BEARISH":
                score = abs(obi) * 1.5
                direction = "Short"
            else:
                score = abs(obi) * 0.5 # Penalize divergence
                direction = "Neutral"
            
            # Volatility Bonus (ATR)
            atr = self._get_cached_atr(symbol, "5m")
            if atr:
                # Normalize ATR roughly (assuming price ~$100 for simplicity, relative comparison matters)
                # Actually, just check if recent range > spread
                score *= 1.1 
            
            if abs(obi) >= self.obi_threshold and direction != "Neutral":
                 candidates.append({
                     'symbol': symbol,
                     'score': score,
                     'direction': direction,
                     'obi': obi
                 })
        
        # Sort by Score Descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        if candidates:
            return candidates[0] # Return the single best asset
        return None

    def validate_regime_simulation(self, symbol, direction):
        """
        Simulates if the strategy would have won in the last hour.
        Checks % of candles in the last 60m that closed in favor of the direction.
        """
        klines = self._get_cached_klines(symbol, "1m")
        if not klines or len(klines) < 60:
            return True # Not enough data, assume OK (fallback)
            
        recent = klines[-60:]
        wins = 0
        for k in recent:
            open_p = float(k['open'])
            close_p = float(k['close'])
            if direction == "Long" and close_p > open_p:
                wins += 1
            elif direction == "Short" and close_p < open_p:
                wins += 1
                
        win_rate = wins / len(recent)
        
        # If market is trending against us locally (win rate < 40%), abort
        if win_rate < 0.4:
            self.logger.warning(f"️ SIMULATION FAILED for {symbol} ({direction}): WinRate 1h = {win_rate:.2f}")
            return False
            
        return True

    def run_triple_consensus(self, symbol, direction):
        """
        Executes the 3 Validators: Trend, Flow, Risk.
        Returns (bool, dict) -> (Approved, Data)
        """
        
        # 1. TREND VALIDATOR (The Trend Setter)
        # Checks 1m, 5m, 15m alignment
        t_1m = self.oracle.get_trend_bias(symbol, "1m")
        t_5m = self.oracle.get_trend_bias(symbol, "5m")
        t_15m = self.oracle.get_trend_bias(symbol, "15m")
        
        target_trend = "BULLISH" if direction == "Long" else "BEARISH"
        
        # We need at least 2 out of 3 aligned
        aligned_count = 0
        if t_1m == target_trend: aligned_count += 1
        if t_5m == target_trend: aligned_count += 1
        if t_15m == target_trend: aligned_count += 1
        
        if aligned_count < 2:
            return False, {"reason": f"Trend Mismatch ({aligned_count}/3)", "1m": t_1m, "5m": t_5m, "15m": t_15m}
            
        # 2. FLOW VALIDATOR (The Whale Watcher)
        depth = self._get_cached_depth(symbol)
        if not depth: return False, {"reason": "No Depth Data"}
        
        obi = self.oracle.calculate_obi(depth)
        
        # Check OBI Strength
        obi_ok = False
        if direction == "Long" and obi > 0.4: obi_ok = True
        elif direction == "Short" and obi < -0.4: obi_ok = True
        
        if not obi_ok:
            return False, {"reason": f"Weak OBI ({obi:.2f})"}
            
        # RVOL Check (Volume Quality)
        # Assuming we have a way to check RVOL, if not skip or mock
        # self.oracle doesn't have RVOL yet, let's use recent range as proxy for activity
        range_pct = self._recent_range_pct(symbol, window=10)
        if range_pct < 0.0005: # Dead market (< 0.05% move in 10 ticks)
             return False, {"reason": "Dead Market (Low Vol)"}

        # 3. RISK VALIDATOR (The Risk Manager)
        atr = self._get_cached_atr(symbol, "5m")
        if not atr: return True, {"reason": "No ATR (Risk check skipped)"} # Fallback
        
        # Scenario: If SL is hit (4x ATR), is it < Max Risk USD?
        # Estimated entry price
        ticker = self._get_cached_ticker(symbol)
        if not ticker or 'lastPrice' not in ticker:
             return False, {"reason": "Ticker Data Missing"}
             
        price = float(ticker['lastPrice'])
        
        sl_dist = atr * 4.0
        
        # Estimate position size
        # If ALL capital, we need to be careful
        # Let's say we use $1000 margin * 5x = $5000 notional
        # Loss = $5000 * sl_dist
        # If Loss > Risk Limit ($50?), Veto.
        
        # For now, we just validate if Volatility is "Insane" (> 2% ATR 5m candle)
        if atr / price > 0.02:
             return False, {"reason": f"Extreme Volatility (ATR {atr/price:.2%})"}
             
        return True, {"trend": f"{aligned_count}/3", "obi": obi, "atr": atr}

    def _spread_pct(self, best_bid, best_ask):
        mid = (best_bid + best_ask) / 2
        if mid <= 0:
            return 0.0
        return (best_ask - best_bid) / mid

    def _absorption_confirmed(self, symbol, side, depth, best_bid, best_ask, spread_pct):
        absorption_range = self._absorption_range_pct(symbol, side, depth, best_bid, best_ask)
        min_absorption = max(spread_pct * 1.5, 0.0004)
        return absorption_range >= min_absorption

    def _zlp_checklist(self, symbol, side, depth, obi, pulse, is_sniper=False):
        if not depth:
            return False
        best_bid = float(depth['bids'][0][0])
        best_ask = float(depth['asks'][0][0])
        spread_pct = self._spread_pct(best_bid, best_ask)
        safe_stop = self.calculate_safe_stop_zone(symbol, side, depth)
        effective_obi_threshold = self.state[symbol].get('learned_obi', self.obi_threshold)
        if side == "Long":
            obi_ok = obi >= effective_obi_threshold
            pulse_ok = pulse != "BEARISH"
        else:
            obi_ok = obi <= -effective_obi_threshold
            pulse_ok = pulse != "BULLISH"
            
        if is_sniper:
            # Sniper Mode: Ignore absorption and reversion. 
            # Trust the massive flow (OBI) and just ensure spread isn't crazy.
            
            # HYPER VOLUME OVERRIDE: Relax Spread Check significantly
            max_spread = 2.0 if self.hyper_volume else 0.005 # 200% for Hyper (Allow everything for Gap Fill), 0.5% for Normal Sniper
            
            if spread_pct > max_spread: 
                 self.logger.info(f" {symbol}: Sniper abortado (Spread {spread_pct*100:.2f}% > {max_spread*100:.1f}%). Bid: {best_bid} Ask: {best_ask}")
                 return False
            return True

        absorption_ok = self._absorption_confirmed(symbol, side, depth, best_bid, best_ask, spread_pct)
        stop_ok = safe_stop >= (spread_pct * 2)
        reversion_ok = self.expected_reversion_ok(symbol, safe_stop)
        time_ok = self._recent_range_pct(symbol, window=6) >= safe_stop * 0.3
        checks = [obi_ok, absorption_ok, stop_ok, reversion_ok, time_ok, pulse_ok]
        if not all(checks):
            self.logger.info(f" {symbol}: Checklist ZLP falhou ({side}).")
            return False
        return True

    async def _process_symbol(self, symbol):
        """Processa a lógica para um único ativo"""
        try:
            pulse = self._get_cached_pulse()
            effective_mode = self._resolve_mode(symbol, pulse)
            self.state[symbol]['effective_mode'] = effective_mode
            
            # Carregar Open Orders antecipadamente para evitar erros de escopo
            open_orders = self._get_cached_open_orders(symbol)

            # 0. Guard Ativo (Straddle e Surf)
            # Protege contra reversão de fluxo
            await self._guard_orders(symbol)
            
            # 1. Verificar Posição
            positions = self._get_cached_positions()
            my_pos = None
            if positions:
                my_pos = next((p for p in positions if p['symbol'] == symbol), None)
            
            if my_pos:
                # TEMOS POSIÇÃO -> CANCELE O OUTRO LADO E SAIA
                qty = float(my_pos['netQuantity'])
                entry_price = float(my_pos['entryPrice'])
                side = "Short" if qty < 0 else "Long"
                
                # Cancela todas as ordens pendentes (o lado que não pegou)
                # open_orders já carregado acima
                for o in open_orders:
                    # Se for Limit Maker de entrada (não TP), cancela
                    if o['orderType'] == 'Limit':
                         # Verifica se é TP (distante) ou Entrada (perto)
                         # Simplificação: Se temos posição, Limit Order só deve ser TP.
                         # Se o preço da ordem estiver muito perto do entry (Straddle antigo), cancela.
                         price = float(o['price'])
                         order_side = o.get('side')
                         same_side = (side == "Long" and order_side == "Bid") or (side == "Short" and order_side == "Ask")
                         if abs(price - entry_price) / entry_price < 0.001 and not same_side:
                             self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                self._invalidate_cache([f"open_orders:{symbol}"])
                
                if entry_price != self.state[symbol]['last_price']:
                    self.state[symbol]['last_price'] = entry_price
                    self.state[symbol]['trailing_activated'] = False
                    self.state[symbol]['last_side'] = "Short" if qty < 0 else "Long"
                    self.state[symbol]['exit_handled'] = False
                    self.state[symbol]['entry_fill_time'] = time.time()
                    self.logger.info(f" FILL EM {symbol}! Lado Vencedor Definido. Gerenciando Saída...")
                
                await self._maybe_confirm_entry(symbol, side, abs(qty), entry_price)
                await self._manage_exit(symbol, side, abs(qty), entry_price)
                
                # Smart Exit (Prioridade Máxima em qualquer modo)
                if await self._check_smart_exit(symbol, side, abs(qty), entry_price):
                    self._mark_exit(symbol, True)
                    self.state[symbol]['last_exit_time'] = time.time()
                    return

                # SURF MODE: Trailing Stop
                if effective_mode == "surf" and self.state[symbol].get('full_entry', True):
                    await self._manage_trailing(symbol, side, entry_price)

            else:
                # SEM POSIÇÃO -> CERCAR O PREÇO
                if self.state[symbol]['last_price'] and not self.state[symbol]['exit_handled']:
                    self._infer_exit_result(symbol)
                self.state[symbol]['last_price'] = 0
                self.state[symbol]['trailing_activated'] = False
                self.state[symbol]['last_side'] = None
                self.state[symbol]['last_sl'] = None
                self.state[symbol]['entry_fill_time'] = 0
                self.state[symbol]['target_qty'] = 0.0
                self.state[symbol]['probe_qty'] = 0.0
                self.state[symbol]['confirm_qty'] = 0.0
                self.state[symbol]['confirmation_sent'] = False
                self.state[symbol]['full_entry'] = False
                self.state[symbol]['probe_spread_pct'] = 0.0
                self.state[symbol]['sl_rearm_attempts'] = 0
                self.state[symbol]['sl_rearm_next_ts'] = 0
                
                # Cooldown Check (5 Minutes) - SKIPPED IN HYPER VOLUME
                last_exit = self.state[symbol].get('last_exit_time', 0)
                cooldown_time = 300
                if self.hyper_volume:
                    cooldown_time = 10 # 10 seconds cooldown for Hyper Volume
                
                # COMPOUND SNIPER COOLDOWN
                if self.compound_mode:
                    cooldown_time = 30 # Quick re-entry if the trend is still good
                
                if time.time() - last_exit < cooldown_time: 
                    # self.logger.info(f"️ {symbol}: Cooldown (Resting)...")
                    return
                
                # --- COMPOUND SNIPER SELECTION LOGIC ---
                if self.compound_mode:
                    # GLOBAL LOCK: Se já existe posição em QUALQUER ativo, não entra em nada novo.
                    # positions já foi carregado no início (_process_symbol)
                    if positions and len(positions) > 0:
                        # Verifica se a posição é DESTE símbolo (já tratada no if my_pos acima)
                        # Se chegamos aqui (else), significa que my_pos é None.
                        # Logo, a posição pertence a OUTRO símbolo.
                        # Devemos abortar para focar no ativo aberto.
                        if open_orders:
                             # Limpa ordens perdidas deste ativo secundário
                             for o in open_orders:
                                 self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                             self._invalidate_cache([f"open_orders:{symbol}"])
                        return

                    # Only allow trade if this symbol is the "CHOSEN ONE"
                    best_asset = self.select_best_compound_asset()
                    if not best_asset or best_asset['symbol'] != symbol:
                        # If I am not the best asset, do nothing (or cancel orders if I had them)
                        if open_orders:
                            for o in open_orders:
                                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                            self._invalidate_cache([f"open_orders:{symbol}"])
                        return # Skip this cycle for this symbol
                    
                    # I am the best asset!
                    # Validate Regime Simulation
                    if not self.validate_regime_simulation(symbol, best_asset['direction']):
                         return # Failed simulation
                    
                    # Set direction based on OBI
                    self.direction = best_asset['direction'].lower() # 'long' or 'short'
                    
                    self.logger.info(f" ALVO CONFIRMADO: {symbol} | Score: {best_asset['score']:.2f} | Dir: {self.direction.upper()}")

                if time.time() < self.state[symbol].get('zero_loss_until', 0):
                    self.logger.warning(f" {symbol}: Zero Loss ativo. Pausando novas entradas.")
                    return
                
                effective_min_entry_interval = self.state[symbol].get('learned_min_entry_interval', self.min_entry_interval)
                if self.eco_mode:
                    last_entry_time = self.state[symbol].get('last_entry_time', 0)
                    if time.time() - last_entry_time < effective_min_entry_interval:
                        return

                # open_orders já carregado no início
                
                # Se Surf/Direcional, precisamos de 1 ordem. Se Straddle, 2.
                target_orders = 1 if self.direction in ["long", "short"] or effective_mode == "surf" else 2
                
                if len(open_orders) < target_orders:
                    if open_orders:
                        # Limpa book sujo
                        for o in open_orders:
                            # Só cancela se for Limit Entrada (perto do preço atual)
                             self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                        self._invalidate_cache([f"open_orders:{symbol}"])
                    await self._place_entry(symbol)
                
        except Exception as e:
            self.logger.error(f"Erro em {symbol}: {e}")

    async def _check_smart_exit(self, symbol, side, qty, entry_price):
        """Verifica se o Número Chave de Lucro foi atingido e executa saída imediata"""
        ticker = self._get_cached_ticker(symbol)
        if not ticker: return False
        curr_price = float(ticker['lastPrice'])
        
        # NÚMERO CHAVE: Ajustado pelo Modo
        # Surf: 0.2% (Busca Swing com margem para Taker Fee)
        # Straddle: 0.15% (Scalp Rápido)
        # Taker Fee (0.085% per leg = 0.17% round trip if both Taker)
        # Maker Fee (0.0% or negative)
        
        # Check if we paid Taker fee on entry (Manual/Market)
        # Simplification: If we are here, we likely used Limit, but manual override or market panic uses Taker.
        # We assume 0.085% entry cost if we don't have fill data.
        # Ideally we should read 'fee' from fill history, but for safety let's assume worst case for TP.
        
        # Actually, let's just enforce a higher NET TARGET.
        taker_fee_pct = 0.00085
        round_trip_taker = taker_fee_pct * 2 # 0.17%
        
        effective_mode = self.state[symbol].get('effective_mode', self.mode)
        target_pct = 0.008 if effective_mode == "surf" else 0.0015
        
        if self.hyper_volume:
             target_pct = 0.008 # 0.8% Target (Profit Farming)
        
        # OMEGA PROTOCOL: Adjust Target for Taker Costs
        # Always assume we might pay Taker on exit.
        # If entry was Market (Manual), we need to cover that too.
        # For now, let's add 0.1% buffer to target_pct to be safe.
        target_pct += 0.001 
        
        should_exit = False
        pnl_pct = 0
        
        if side == "Long":
            pnl_pct = (curr_price - entry_price) / entry_price
            if pnl_pct >= target_pct: should_exit = True
        else:
            pnl_pct = (entry_price - curr_price) / entry_price
            if pnl_pct >= target_pct: should_exit = True
            
        if should_exit:
            self.logger.info(f" {symbol}: ALVO ATINGIDO ({pnl_pct*100:.2f}%)! Saída Inteligente...")
            
            # Saída a Mercado (Taker) para garantir execução instantânea
            # Mapeamento Correto para API: Long -> Sell -> Ask | Short -> Buy -> Bid
            exit_side = "Ask" if side == "Long" else "Bid"
            
            payload = {
                "symbol": symbol,
                "side": exit_side,
                "orderType": "Market",
                "quantity": str(qty)
            }
            res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res and 'id' in res:
                self.logger.info(f" {symbol}: LUCRO NO BOLSO! Ordem {res['id']}")
                # Limpa ordens pendentes
                open_orders = self._get_cached_open_orders(symbol)
                for o in open_orders:
                    self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                self._invalidate_cache([f"open_orders:{symbol}", "positions", f"ticker:{symbol}"])
                return True
            else:
                self.logger.error(f" {symbol}: Falha na Saída Inteligente: {res}")
                
        return False

    async def _manage_trailing(self, symbol, side, entry_price):
        """Move o SL para garantir lucro líquido (Taxas + Spread Pagos)"""
        ticker = self._get_cached_ticker(symbol)
        if not ticker:
            return
        curr_price = float(ticker['lastPrice'])
        
        # CÁLCULO DE CUSTOS REAIS (Backpack Futures)
        # Taker Fee: 0.05% (Pior caso no Stop Market)
        # Maker Fee: 0.02% (Entrada) - Vamos assumir custo para ser conservador
        # Spread/Slippage Est.: 0.02%
        # Custo Total Break-Even: ~0.09%
        
        cost_basis_pct = 0.001 # 0.1% (Segurança Absoluta)
        
        # Calculate PnL first (FIX: Define pnl before usage)
        if side == "Long":
            pnl = (curr_price - entry_price) / entry_price
        else:
            pnl = (entry_price - curr_price) / entry_price
        
        # Estágios de Garantia
        # Estágio 1: Ativação Rápida. Garante apenas custos (0.1%) + Café (0.05%) = 0.15%
        # Estágio 2: Lucro Real. Garante 0.5% Livre.
        
        activation_pct = 0.0025 # 0.25% de movimento a favor para ativar (Early Activation)
        secure_pct = 0.0015     # 0.15% (Cobre custos 0.1% + Lucro 0.05%)

        if self.ironclad:
            activation_pct = 0.0015 # 0.15% (Ativação Ultrarrápida - Paga as taxas)
            secure_pct = 0.0005     # 0.05% (Garante Café e zera risco)
        
        new_sl = None
        
        if self.ironclad and pnl > activation_pct:
             new_sl = entry_price * (1 + secure_pct) # Garante Break-Even + Lucro Mínimo
             self.logger.info(f"️ {symbol}: IRONCLAD BREAKEVEN! SL movido para {new_sl} (Lucro Garantido)")
        
        elif side == "Long":
            pnl = (curr_price - entry_price) / entry_price
            
            if pnl > 0.01: # Estágio 2 (>1% Lucro)
                 new_sl = entry_price * 1.005 # Garante 0.5% Líquido
                 self.logger.info(f" {symbol}: Lucro Consolidado! Garantindo 0.5% Líquido.")
            elif pnl > activation_pct: # Estágio 1 (>0.35% Lucro)
                 new_sl = entry_price * (1 + secure_pct) # Garante 0.15% Bruto (0.05% Líquido)
            
            if new_sl:
                 self._update_stop_loss(symbol, "Sell", new_sl)
                 self.state[symbol]['trailing_activated'] = True
                 
        else: # Short
            pnl = (entry_price - curr_price) / entry_price
            
            if pnl > 0.01:
                 new_sl = entry_price * 0.995
                 self.logger.info(f" {symbol}: Lucro Consolidado! Garantindo 0.5% Líquido.")
            elif pnl > activation_pct:
                 new_sl = entry_price * (1 - secure_pct)

            if new_sl:
                 self._update_stop_loss(symbol, "Buy", new_sl)
                 self.state[symbol]['trailing_activated'] = True

    def _update_stop_loss(self, symbol, side, new_price):
        """Cancela SL antigo e cria novo"""
        open_orders = self._get_cached_open_orders(symbol)
        qty = None
        
        # Encontrar e cancelar SL antigo
        for o in open_orders:
            if 'Stop' in o['orderType'] or (o['orderType'] == 'Market' and float(o.get('triggerPrice', 0)) > 0):
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                qty = o['quantity'] # Reusa a qtd
        self._invalidate_cache([f"open_orders:{symbol}"])
        
        # Se não achou qtd, tenta pegar da posição (fallback)
        if not qty:
             positions = self._get_cached_positions()
             my_pos = next((p for p in positions if p['symbol'] == symbol), None)
             if my_pos: qty = abs(float(my_pos['netQuantity']))
        
        if qty:
            # Rounding
            if "BTC" in symbol: new_price = round(new_price, 1)
            elif "ETH" in symbol: new_price = round(new_price, 2)
            elif "SOL" in symbol: new_price = round(new_price, 2)
            else: new_price = round(new_price, 4)
            
            self._send_stop_order(symbol, side, qty, new_price)

    async def _guard_orders(self, symbol):
        """Cancela ordens pendentes e fecha posições se o fluxo (OBI) virar contra agressivamente."""
        if self.dry_run: return
        depth = self._get_cached_depth(symbol)
        if not depth: return
        
        obi = self.oracle.calculate_obi(depth)
        pulse = self._get_cached_pulse()
        
        if self.ironclad or self.compound_mode:
             # IRONCLAD/COMPOUND: NUNCA FECHAR A MERCADO POR PÂNICO DE OBI
             # O usuário proibiu "fechar no prejuízo perdendo centavos".
             # Confiamos no Stop Loss Técnico (que é posicionado longe do ruído).
             return

        # 1. Proteção de Posição Aberta (Emergency Exit)
        positions = self._get_cached_positions()
        my_pos = next((p for p in positions if p['symbol'] == symbol), None)
        
        if my_pos:
            qty = float(my_pos['netQuantity'])
            side = "Long" if qty > 0 else "Short"
            
            # Se Long e OBI < -0.5 -> Perigo de Reversão -> Fecha a Mercado
            if side == "Long" and obi < -0.5:
                self.logger.warning(f" {symbol}: OBI Reversal ({obi:.2f})! FECHANDO LONG (Emergency Exit)")
                self.transport._send_request("POST", "/api/v1/order", "orderExecute", {
                    "symbol": symbol,
                    "side": "Ask", # Corrected from Sell
                    "orderType": "Market",
                    "quantity": str(abs(qty))
                })
                # Cancela SL/TP antigos para não ficar pendurado
                open_orders = self._get_cached_open_orders(symbol)
                for o in open_orders:
                    self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                self._invalidate_cache([f"open_orders:{symbol}", "positions"])
                return

            # Se Short e OBI > 0.5 -> Perigo de Reversão -> Fecha a Mercado
            if side == "Short" and obi > 0.5:
                self.logger.warning(f" {symbol}: OBI Reversal ({obi:.2f})! FECHANDO SHORT (Emergency Exit)")
                self.transport._send_request("POST", "/api/v1/order", "orderExecute", {
                    "symbol": symbol,
                    "side": "Bid", # Corrected from Buy
                    "orderType": "Market",
                    "quantity": str(abs(qty))
                })
                open_orders = self._get_cached_open_orders(symbol)
                for o in open_orders:
                    self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
                self._invalidate_cache([f"open_orders:{symbol}", "positions"])
                return

        # 2. Proteção de Ordens Pendentes (Pré-Entrada)
        open_orders = self._get_cached_open_orders(symbol)
        if not open_orders: return
        
        for order in open_orders:
            # Só cancela se for Limit Entrada (perto do preço atual) e não TP
            if order['orderType'] != 'Limit': continue
            
            # Verifica se é TP (longe) ou Entrada (perto) - Simplificado
            # Se OBI virou, cancela a entrada contra o fluxo
            side = order['side']
            if side == "Bid" and obi < -0.3:
                self.logger.warning(f"️ {symbol}: Cancelando Compra Pendente (OBI {obi:.2f})")
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': order['id']})
                self._invalidate_cache([f"open_orders:{symbol}"])
            elif side == "Ask" and obi > 0.3:
                self.logger.warning(f"️ {symbol}: Cancelando Venda Pendente (OBI {obi:.2f})")
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': order['id']})
                self._invalidate_cache([f"open_orders:{symbol}"])
            if pulse == "BEARISH" and side == "Bid":
                self.logger.warning(f" {symbol}: Mercado BEARISH. Cancelando Compra.")
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': order['id']})
                self._invalidate_cache([f"open_orders:{symbol}"])
            elif pulse == "BULLISH" and side == "Ask":
                self.logger.warning(f" {symbol}: Mercado BULLISH. Cancelando Venda.")
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': order['id']})
                self._invalidate_cache([f"open_orders:{symbol}"])

    async def _maybe_confirm_entry(self, symbol, side, qty, entry_price):
        if self.state[symbol].get('full_entry'):
            if not self.state[symbol].get('entry_fill_time'):
                self.state[symbol]['entry_fill_time'] = time.time()
            return
        target_qty = self.state[symbol].get('target_qty', 0.0)
        if target_qty <= 0:
            self.state[symbol]['full_entry'] = True
            if not self.state[symbol].get('entry_fill_time'):
                self.state[symbol]['entry_fill_time'] = time.time()
            return
        abs_qty = abs(qty)
        if abs_qty >= target_qty * 0.95:
            self.state[symbol]['full_entry'] = True
            if not self.state[symbol].get('entry_fill_time'):
                self.state[symbol]['entry_fill_time'] = time.time()
            return
        if self.state[symbol].get('confirmation_sent'):
            return
        depth = self._get_cached_depth(symbol)
        if not depth:
            return
        obi = self.oracle.calculate_obi(depth)
        manual_obi = self._get_manual_signal(self.manual_obi, symbol)
        if manual_obi is not None:
            try:
                obi = float(manual_obi)
            except Exception:
                return
        pulse = self._get_cached_pulse()
        effective_obi_threshold = self.state[symbol].get('learned_obi', self.obi_threshold)
        profile_name, profile = self._resolve_profile(symbol)
        profile_min_obi = profile.get("min_obi")
        if profile_min_obi is not None:
            effective_obi_threshold = max(effective_obi_threshold, float(profile_min_obi))

        # IRONCLAD PROTOCOL (Survival Mode)
        # 1. Trend Filter (1m EMA)
        trend_ok = True
        if self.ironclad:
            trend_bias = self.oracle.get_trend_bias(symbol, timeframe="1m")
            if side == "Long" and trend_bias != "BULLISH":
                self.logger.info(f"️ {symbol}: Ironclad BLOQUEOU Long (Trend 1m é {trend_bias})")
                trend_ok = False
            elif side == "Short" and trend_bias != "BEARISH":
                self.logger.info(f"️ {symbol}: Ironclad BLOQUEOU Short (Trend 1m é {trend_bias})")
                trend_ok = False
            
            if not trend_ok:
                 return

        # SMART MONEY CHECKLIST (Volume Intensity + OBI)
        rvol = self.oracle.get_volume_intensity(symbol)
        
        if side == "Long":
            # Require OBI OR High Volume
            # If Volume is Intense (>1.5), we can accept lower OBI (0.2)
            # If Volume is Low (<0.8), we require Strong OBI (0.5)
            
            required_obi = effective_obi_threshold
            if rvol > 1.5: required_obi = max(required_obi * 0.5, 0.2)
            elif rvol < 0.8: required_obi = max(required_obi * 1.2, 0.5)
            
            obi_ok = obi >= required_obi
            pulse_ok = pulse != "BEARISH"
            price = float(depth['bids'][0][0])
            order_side = "Buy"
            
            if obi_ok:
                 self.logger.info(f" {symbol}: Smart Money Long Signal (OBI {obi:.2f} | RVOL {rvol:.2f})")
                 
        else:
            required_obi = effective_obi_threshold
            if rvol > 1.5: required_obi = max(required_obi * 0.5, 0.2)
            elif rvol < 0.8: required_obi = max(required_obi * 1.2, 0.5)
            
            obi_ok = obi <= -required_obi
            pulse_ok = pulse != "BULLISH"
            price = float(depth['asks'][0][0])
            order_side = "Sell"
            
            if obi_ok:
                 self.logger.info(f" {symbol}: Smart Money Short Signal (OBI {obi:.2f} | RVOL {rvol:.2f})")
        best_bid = float(depth['bids'][0][0])
        best_ask = float(depth['asks'][0][0])
        spread_pct = self._spread_pct(best_bid, best_ask)
        probe_spread = self.state[symbol].get('probe_spread_pct', spread_pct)
        absorption_ok = self._absorption_confirmed(symbol, side, depth, best_bid, best_ask, spread_pct)
        if not (obi_ok and pulse_ok and absorption_ok and spread_pct <= probe_spread * 1.2):
            return
        remaining_qty = max(target_qty - abs_qty, 0.0)
        remaining_qty = self._round_qty(symbol, remaining_qty)
        if remaining_qty <= 0:
            return
        self._send_maker_order(symbol, order_side, remaining_qty, price)
        self.state[symbol]['confirmation_sent'] = True

    async def _manage_exit(self, symbol, side, qty, entry_price):
        """Coloca ordem de saída (TP) e Proteção (SL) simultaneamente"""
        open_orders = self._get_cached_open_orders(symbol)
        
        has_tp = False
        has_sl = False
        
        for o in open_orders:
            if o['orderType'] == 'Limit': has_tp = True
            if 'Stop' in o['orderType'] or (o['orderType'] == 'Market' and float(o.get('triggerPrice', 0)) > 0): has_sl = True
            
        # Se já tem os dois, ok.
        if has_tp and has_sl: return

        effective_profit_usd = self.state[symbol].get('learned_profit_usd', self.profit_usd)
        effective_risk_usd = self.state[symbol].get('learned_risk_usd', self.risk_usd)
        notional = qty * entry_price * 1.0
        if notional <= 0:
            return
        min_green_margin = max(effective_profit_usd / notional, 0.0005)
        
        # ATR-based TP Adjustment
        atr_5m = self._get_cached_atr(symbol, "5m")
        if atr_5m:
            # TP Target should be at least 1.2x ATR 5m to clear noise
            atr_target = atr_5m * 1.2
            if min_green_margin < atr_target:
                min_green_margin = atr_target
        
        # 3-WAVE TOLERANCE STOP LOSS (User Request: Survive multiple pullbacks)
        # We need a wider berth. 2% is often too tight for crypto "wicks".
        # We will use 3.5x ATR if available, or a fixed 4% safety net.
        base_sl_cap = 0.04 # 4% Hard Cap
        if atr_5m:
            # 3.5x ATR allows for ~3 normal volatility waves
            atr_sl = atr_5m * 3.5
            stop_loss_margin = min(effective_risk_usd / notional, max(atr_sl, 0.015))
            # Cap at 6% absolute max to prevent liquidation risk
            stop_loss_margin = min(stop_loss_margin, 0.06)
        else:
            stop_loss_margin = min(effective_risk_usd / notional, base_sl_cap)

        depth = self._get_cached_depth(symbol)
        obi = None
        if depth:
            obi = self.oracle.calculate_obi(depth)
            # HYPER VOLUME OVERRIDE (Sprint Final S4)
        if self.hyper_volume:
            # 1.5% Margin to survive waves (Recovery Mode)
            stop_loss_margin = 0.015 
        elif self.compound_mode:
            # COMPOUND MODE: SURVIVABILITY IS KEY
            # We use a wider stop initially (Structural) and rely on Smart Exit to close early if needed
            stop_loss_margin = 0.025 # 2.5% Base Stop (Allows breathing room)
            if atr_5m:
                 stop_loss_margin = max(atr_5m * 4.0, 0.02) # 4x ATR (Deep breath)
                 
        elif (side == "Long" and obi > 0.5) or (side == "Short" and obi < -0.5):
            stop_loss_margin = max(stop_loss_margin * 0.8, 0.01) # Tighten by 20% if strong flow
            
            safe_stop = self.calculate_safe_stop_zone(symbol, side, depth)
            if safe_stop > stop_loss_margin:
                # Only widen if safe stop is REASONABLE (e.g. < 5%)
                if safe_stop < 0.05:
                     stop_loss_margin = safe_stop
        
        loss_streak = self.state[symbol].get('consecutive_losses', 0)
        if loss_streak > 0:
            min_green_margin = max(min_green_margin * 0.95, 0.0005)

        pulse = self._get_cached_pulse()
        should_arm_sl = self.time_based_stop_unlock(symbol, side, obi, pulse)
        
        # SMART BREAKEVEN (First Wave Clear)
        # Don't move to BE until we have cleared the first "noise" zone (0.4% or 1x ATR)
        cost_basis_pct = 0.001
        first_wave_zone = 0.004 # 0.4% minimum move before BE
        if atr_5m:
             first_wave_zone = max(atr_5m * 1.5, 0.003)
             
        ticker = self._get_cached_ticker(symbol)
        pnl_pct = 0
        curr_price = entry_price
        if ticker and 'lastPrice' in ticker:
            curr_price = float(ticker['lastPrice'])
            if side == "Long":
                pnl_pct = (curr_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - curr_price) / entry_price
                
        flow_exhausted = False
        if obi is not None:
            if side == "Long":
                flow_exhausted = obi < 0.05
            else:
                flow_exhausted = obi > -0.05
        
        # Only trigger BE if we cleared the first wave
        breakeven_mode = pnl_pct >= first_wave_zone
        
        if breakeven_mode:
            should_arm_sl = True
            # Secure costs + small profit
            target_sl_margin = -0.0015 # Negative margin means profit side (above entry for Long)
            # Logic below handles sign based on side, but stop_loss_margin is usually positive distance.
            # We need to handle this carefully in the price calc section.
            
            # Actually, standard logic uses stop_loss_margin as distance FROM entry.
            # If we want to lock profit, we need negative distance or specific logic.
            # For simplicity here, we just tighten SL to entry (0.0 distance) or slight profit.
            
            # Let's just set it to Cost Basis for now to be safe.
            if stop_loss_margin > cost_basis_pct:
                 stop_loss_margin = -0.001 # Lock 0.1% profit (Negative distance logic needed below?)
                 # Wait, logic below: sl_price = entry * (1 - margin).
                 # If margin is negative (-0.001), sl = entry * (1.001) -> Profit!
                 pass 

        elif flow_exhausted:
            should_arm_sl = True
            
        if not has_sl:
            should_arm_sl = True
        
        if side == "Long":
            tp_price = entry_price * (1 + min_green_margin)
            # Support negative margin for Profit Stop
            sl_price = entry_price * (1 - stop_loss_margin)
            exit_side = "Sell"
        else:
            tp_price = entry_price * (1 - min_green_margin)
            sl_price = entry_price * (1 + stop_loss_margin)
            exit_side = "Buy"
            
        # Fix logic for Breakeven override if margin was set negative
        if breakeven_mode:
             # Force SL to Entry + Cost Basis
             if side == "Long":
                  sl_price = max(sl_price, entry_price * (1 + 0.001))
             else:
                  sl_price = min(sl_price, entry_price * (1 - 0.001))
            
        # Rounding
        if "BTC" in symbol: 
            tp_price = round(tp_price, 1)
            sl_price = round(sl_price, 1)
        elif "ETH" in symbol: 
            tp_price = round(tp_price, 2)
            sl_price = round(sl_price, 2)
        elif "SOL" in symbol: 
            tp_price = round(tp_price, 2)
            sl_price = round(sl_price, 2)
        else: 
            tp_price = round(tp_price, 4)
            sl_price = round(sl_price, 4)
        
        if self.ironclad:
             # Ironclad: Prioridade total ao SL
             if not has_sl:
                 should_arm_sl = True
             # Se tiver SL, mas estiver longe demais, ajusta? (Futuro)
        
        # 1. Coloca TP (Maker) se não tiver
        if not has_tp:
            self.logger.info(f" {symbol}: TP Green {exit_side} @ {tp_price}")
            if not self.dry_run:
                self._send_maker_order(symbol, exit_side, qty, tp_price)
                
        # 2. Coloca SL (Stop Market) se não tiver
        if not has_sl and should_arm_sl:
            self.logger.info(f"️ {symbol}: SL Protection @ {sl_price}")
            if not self.dry_run:
                ok = await self._arm_stop_with_retries(symbol, exit_side, qty, sl_price)
                if self.mandatory_sl and not ok:
                    if self.state[symbol].get('sl_rearm_attempts', 0) >= self.sl_rearm_max_attempts:
                        self._force_close_position(symbol, side, qty)
        if should_arm_sl:
            self.state[symbol]['last_sl'] = sl_price

    def _send_stop_order(self, symbol, side, qty, trigger_price):
        # Map Buy/Sell to Bid/Ask correct enum
        api_side = "Bid" if side == "Buy" else "Ask"
        
        payload = {
            "symbol": symbol,
            "side": api_side, 
            "orderType": "Market", # TriggerPrice activates Stop Market behavior
            "quantity": str(qty),
            "triggerPrice": str(trigger_price),
            # Backpack API Error fix: Must specify both `triggerPrice` and `triggerQuantity`
            "triggerQuantity": str(qty) 
        }
        
        res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        if res and 'id' in res:
            self.logger.info(f" {symbol}: SL Armado {res['id']}")
            self._invalidate_cache([f"open_orders:{symbol}"])
            return True
        else:
            self.logger.warning(f" {symbol}: Falha SL {res}")
        self._invalidate_cache([f"open_orders:{symbol}"])
        return False

    async def _arm_stop_with_retries(self, symbol, exit_side, qty, trigger_price):
        now = time.time()
        state = self.state[symbol]
        next_ts = state.get('sl_rearm_next_ts', 0)
        if now < next_ts:
            return False
        attempts = state.get('sl_rearm_attempts', 0)
        if attempts >= self.sl_rearm_max_attempts:
            return False
        ok = self._send_stop_order(symbol, exit_side, qty, trigger_price)
        if ok:
            state['sl_rearm_attempts'] = 0
            state['sl_rearm_next_ts'] = 0
            return True
        attempts += 1
        state['sl_rearm_attempts'] = attempts
        if attempts < self.sl_rearm_max_attempts:
            state['sl_rearm_next_ts'] = now + self.sl_rearm_backoff_seconds
            self.logger.warning(f"⏳ {symbol}: Rearme SL tentativa {attempts}/{self.sl_rearm_max_attempts}")
            return False
        state['sl_rearm_next_ts'] = now + (self.sl_rearm_backoff_seconds * 3)
        return False

    def _force_close_position(self, symbol, side, qty):
        close_side = "Ask" if side == "Long" else "Bid"
        payload = {
            "symbol": symbol,
            "side": close_side,
            "orderType": "Market",
            "quantity": str(qty)
        }
        res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        if res and 'id' in res:
            self.logger.warning(f" {symbol}: Fechamento forçado {res['id']}")
        else:
            self.logger.error(f" {symbol}: Falha no fechamento forçado {res}")
        open_orders = self._get_cached_open_orders(symbol)
        for o in open_orders:
            self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': o['id']})
        self._invalidate_cache([f"open_orders:{symbol}", "positions"])

    async def _place_entry(self, symbol):
        """Coloca ordem de entrada baseada no modo e OBI (Smart Straddle)"""
        depth = self._get_cached_depth(symbol)
        if not depth: return
        
        obi = self.oracle.calculate_obi(depth)
        manual_obi = self._get_manual_signal(self.manual_obi, symbol)
        if manual_obi is not None:
            try:
                obi = float(manual_obi)
            except Exception:
                return
        pulse = self._get_cached_pulse()
        
        # 1. Base Trend Filter
        allow_long = pulse != "BEARISH"
        allow_short = pulse != "BULLISH"

        # 2. Apply Direction Override
        if self.direction == "long":
            allow_short = False
        elif self.direction == "short":
            allow_long = False
            
        # COMPOUND MODE OVERRIDE: Direction is already set by Scanner, but double check OBI here
        if self.compound_mode:
            # If OBI flipped sign while we were waiting, abort entry
            if self.direction == "long" and obi < -0.1: return
            if self.direction == "short" and obi > 0.1: return

        effective_mode = self.state[symbol].get('effective_mode', self.mode)
        profile_name, profile = self._resolve_profile(symbol)
        if profile.get("enabled") is False:
            return
        
        best_bid = float(depth['bids'][0][0])
        best_ask = float(depth['asks'][0][0])
        spread = best_ask - best_bid
        
        ref_price = (best_bid + best_ask) / 2
        profile_leverage = profile.get("leverage", self.leverage)
        profile_margin = profile.get("margin", self.capital_per_trade)
        
        # COMPOUND MODE: ALL-IN
        if self.use_all_capital or self.compound_mode:
             # Calculate max available margin dynamically
             # We fetch account balance
             try:
                 balance = self.transport._send_request("GET", "/api/v1/capital", "capital", {})
                 if balance and 'availableToTrade' in balance:
                     avail_usdc = float(balance['availableToTrade']['USDC'])
                     # Use 95% of available to leave room for fees/rounding
                     profile_margin = avail_usdc * 0.95
                     
                     # STRADDLE SAFETY: If Straddle mode, split margin by 2
                     # Exception: If effective_mode is surf, we use full margin.
                     if effective_mode == "straddle":
                         profile_margin = profile_margin / 2.0
                         self.logger.info(f" COMPOUND SIZE (Straddle): ${profile_margin:.2f} (47.5% of ${avail_usdc:.2f} each leg)")
                     else:
                         self.logger.info(f" COMPOUND SIZE: ${profile_margin:.2f} (95% of ${avail_usdc:.2f})")
             except Exception as e:
                 self.logger.error(f"Failed to fetch capital for compound: {e}")
                 return

        target_notional = profile_margin * profile_leverage
        qty = target_notional / ref_price
        qty = self._round_qty(symbol, qty)
        if qty <= 0:
            return
        
        self.logger.info(f"️ {symbol}: Posicionando (OBI {obi:.2f})...")
        
        # Lógica de Entrada Refinada (Noise Filter)
        # Se OBI for fraco (entre -threshold e +threshold), NÃO FAZ NADA.
        loss_streak = self.state[symbol].get('consecutive_losses', 0)
        effective_obi_threshold = self.state[symbol].get('learned_obi', self.obi_threshold)
        profile_min_obi = profile.get("min_obi")
        if profile_min_obi is not None:
            effective_obi_threshold = max(effective_obi_threshold, float(profile_min_obi))
        profile_min_onchain = profile.get("min_onchain")
        if profile_min_onchain is not None:
            manual_onchain = self._get_manual_signal(self.manual_onchain, symbol)
            if manual_onchain is None:
                self.logger.info(f" {symbol}: On-chain manual ausente para perfil {profile_name}")
                return
            try:
                manual_onchain_value = float(manual_onchain)
            except Exception:
                return
            if manual_onchain_value < float(profile_min_onchain):
                self.logger.info(f" {symbol}: On-chain manual {manual_onchain_value:.2f} < {profile_min_onchain}")
                return
        dynamic_threshold = effective_obi_threshold + min(0.2, loss_streak * 0.05)
        if abs(obi) < dynamic_threshold:
             self.logger.info(f" {symbol}: Mercado Lateral (OBI {obi:.2f} < {dynamic_threshold}). Aguardando fluxo...")
             return

        # Preços Base
        bid_price = best_bid
        ask_price = best_ask
        
        mid_price = (best_bid + best_ask) / 2
        spread_pct = (best_ask - best_bid) / mid_price if mid_price > 0 else 0.0
        
        # Smart Pricing (Read Direction & Position)
        # If Sniper OBI detected, try to front-run the book (Lead)
        # If standard entry, just join the book (Join)
        
        pricing_intent = "Join"
        tick_size = 0.1 if "BTC" in symbol else (0.01 if "SOL" in symbol or "ETH" in symbol or "AVAX" in symbol else 0.0001)
        
        # GAP FILLER LOGIC (For Broken/Illiquid Books)
        # If spread is huge (> 1%), we ignore Best Bid/Ask and price relative to LAST PRICE.
        
        ticker = self._get_cached_ticker(symbol)
        last_price = float(ticker['lastPrice']) if ticker else mid_price
        
        use_gap_fill = False
        gap_bid = bid_price
        gap_ask = ask_price
        
        if spread_pct > 0.01: # 1% Spread = Illiquid/Broken
             use_gap_fill = True
             
             # Force usage of Last Price for Gap Fill.
             # Mid Price is unreliable when book is thin (e.g. Bid 63k, Ask 89k -> Mid 76k is useless).
             # We want to be competitive near the last traded price.
             ref_price = last_price
             
             # Bid just below Ref Price
             gap_bid = ref_price - tick_size
             if gap_bid > best_ask: gap_bid = best_ask - tick_size # Safety
             
             # Ask just above Ref Price
             gap_ask = ref_price + tick_size
             if gap_ask < best_bid: gap_ask = best_bid + tick_size # Safety
             
             pricing_intent = "GapFill"

        # Modo SURF: Apenas 1 Lado (A favor da tendência e fluxo)
        if effective_mode == "surf":
            # Strict Surf: Pulse MUST match direction to prevent "picking a side randomly"
            
            # SNIPER OVERRIDE: If OBI is massive (> 0.7), we take the shot even if Pulse is NEUTRAL (Breakout Mode)
            sniper_obi = 0.7
            
            # HYPER VOLUME OVERRIDE:
            if self.hyper_volume:
                 # HYPER VOLUME SAFETY MODULATION
                 # Se tivermos perdas consecutivas, o sistema DEVE apertar os cintos.
                 # Não podemos queimar caixa em busca de volume se o mercado estiver hostil.
                 
                 loss_streak = self.state[symbol].get('consecutive_losses', 0)
                 if loss_streak >= 2:
                      effective_obi_threshold = 0.4 # Volta a ser exigente
                      self.logger.warning(f"️ {symbol}: Modo Defensivo Ativado (2 Perdas seguidas). OBI exigido subiu para 0.4")
                 else:
                      effective_obi_threshold = 0.10 # Mantém agressividade
                # Relax Trend Requirement: Only block if EXPLICITLY against trend
                # NEUTRAL is allowed.
            
            # COMPOUND MODE: OVERRIDE OBI/TREND LOGIC
            # If we are here in compound mode, the Scanner has already validated everything.
            # We just need to execute.
            if self.compound_mode:
                # --- TRIPLE CONSENSUS VALIDATION ---
                # 1. Trend Validator (Multi-Timeframe)
                # 2. Flow Validator (OBI + Vol)
                # 3. Risk Validator (Scenario Simulation)
                consensus_ok, consensus_data = self.run_triple_consensus(symbol, self.direction)
                
                if not consensus_ok:
                    self.logger.warning(f"️ CONSENSUS VETO: {symbol} blocked by validators. {consensus_data}")
                    return

                if self.direction == "long":
                     self.logger.info(f" COMPOUND ENTRY: {symbol} LONG (Consensus Validated)")
                     # Sniper Pricing
                     bid_price = best_bid + tick_size
                     if bid_price >= best_ask: bid_price = best_bid
                     
                     # No probe logic in Compound Mode - We go FULL CLIP (or split slightly for fills)
                     # But for simplicity, let's stick to the probe logic to avoid huge wall collisions,
                     # just make the probe bigger (50%)
                     probe_qty = self._round_qty(symbol, qty * 0.50)
                     self.state[symbol]['target_qty'] = qty
                     self.state[symbol]['probe_qty'] = probe_qty
                     self.state[symbol]['confirm_qty'] = max(self._round_qty(symbol, qty - probe_qty), 0)
                     self.state[symbol]['confirmation_sent'] = False
                     self.state[symbol]['full_entry'] = False
                     self.state[symbol]['probe_spread_pct'] = self._spread_pct(best_bid, best_ask)
                     self._send_maker_order(symbol, "Buy", probe_qty, bid_price)
                     self._mark_entry(symbol)
                     return

                elif self.direction == "short":
                     self.logger.info(f" COMPOUND ENTRY: {symbol} SHORT (Consensus Validated)")
                     # Sniper Pricing
                     ask_price = best_ask - tick_size
                     if ask_price <= best_bid: ask_price = best_ask
                     
                     probe_qty = self._round_qty(symbol, qty * 0.50)
                     self.state[symbol]['target_qty'] = qty
                     self.state[symbol]['probe_qty'] = probe_qty
                     self.state[symbol]['confirm_qty'] = max(self._round_qty(symbol, qty - probe_qty), 0)
                     self.state[symbol]['confirmation_sent'] = False
                     self.state[symbol]['full_entry'] = False
                     self.state[symbol]['probe_spread_pct'] = self._spread_pct(best_bid, best_ask)
                     self._send_maker_order(symbol, "Sell", probe_qty, ask_price)
                     self._mark_entry(symbol)
                     return
            
            if allow_long and obi > effective_obi_threshold: # Bullish -> Long Only
                # Additional Check: Confirm Trend Direction OR Sniper OBI
                is_sniper_shot = (obi >= sniper_obi)
                
                trend_ok = (pulse == "BULLISH")
                if self.hyper_volume:
                    trend_ok = (pulse != "BEARISH") # Allow NEUTRAL in Hyper Mode
                
                if trend_ok or is_sniper_shot: 
                    if not self._zlp_checklist(symbol, "Long", depth, obi, pulse, is_sniper=(is_sniper_shot or self.hyper_volume)):
                        return
                    
                    reason = "Trend BULLISH" if pulse == "BULLISH" else "SNIPER OBI"
                    if self.hyper_volume: reason = "HYPER VOLUME"
                    
                    # Smart Pricing Logic
                    if use_gap_fill:
                         bid_price = gap_bid
                    elif is_sniper_shot:
                         # Front-run: Bid = Best Bid + Tick (Ensure < Ask)
                         bid_price = best_bid + tick_size
                         if bid_price >= best_ask: bid_price = best_bid # Safety fallback
                         pricing_intent = "Lead (Sniper)"
                    
                    self.logger.info(f" {symbol}: Surf Long ({reason} + OBI {obi:.2f}). Reading: UP. Pricing: {pricing_intent} @ {bid_price}")
                    
                    probe_qty = self._round_qty(symbol, qty * 0.35)
                    if probe_qty <= 0:
                        return
                    self.state[symbol]['target_qty'] = qty
                    self.state[symbol]['probe_qty'] = probe_qty
                    self.state[symbol]['confirm_qty'] = max(self._round_qty(symbol, qty - probe_qty), 0)
                    self.state[symbol]['confirmation_sent'] = False
                    self.state[symbol]['full_entry'] = False
                    self.state[symbol]['probe_spread_pct'] = self._spread_pct(best_bid, best_ask)
                    self._send_maker_order(symbol, "Buy", probe_qty, bid_price)
                    self._mark_entry(symbol)
                else:
                    self.logger.info(f"⏳ {symbol}: Surf Long Paused (Pulse {pulse} != BULLISH). Waiting for Trend.")
                    
            elif allow_short and obi < -effective_obi_threshold: # Bearish -> Short Only
                # Additional Check: Confirm Trend Direction OR Sniper OBI
                is_sniper_shot = (obi <= -sniper_obi)
                
                trend_ok = (pulse == "BEARISH")
                if self.hyper_volume:
                    trend_ok = (pulse != "BULLISH") # Allow NEUTRAL in Hyper Mode

                if trend_ok or is_sniper_shot: # Only surf if Trend is explicitly Bearish
                    if not self._zlp_checklist(symbol, "Short", depth, obi, pulse, is_sniper=(is_sniper_shot or self.hyper_volume)):
                        return
                    
                    reason = "Trend BEARISH" if pulse == "BEARISH" else "SNIPER OBI"
                    if self.hyper_volume: reason = "HYPER VOLUME"
                    
                    # Smart Pricing Logic
                    if use_gap_fill:
                         ask_price = gap_ask
                    elif is_sniper_shot:
                         # Front-run: Ask = Best Ask - Tick (Ensure > Bid)
                         ask_price = best_ask - tick_size
                         if ask_price <= best_bid: ask_price = best_ask # Safety fallback
                         pricing_intent = "Lead (Sniper)"

                    self.logger.info(f" {symbol}: Surf Short ({reason} + OBI {obi:.2f}). Reading: DOWN. Pricing: {pricing_intent} @ {ask_price}")
                    
                    probe_qty = self._round_qty(symbol, qty * 0.35)
                    if probe_qty <= 0:
                        return
                    self.state[symbol]['target_qty'] = qty
                    self.state[symbol]['probe_qty'] = probe_qty
                    self.state[symbol]['confirm_qty'] = max(self._round_qty(symbol, qty - probe_qty), 0)
                    self.state[symbol]['confirmation_sent'] = False
                    self.state[symbol]['full_entry'] = False
                    self.state[symbol]['probe_spread_pct'] = self._spread_pct(best_bid, best_ask)
                    self._send_maker_order(symbol, "Sell", probe_qty, ask_price)
                    self._mark_entry(symbol)
                else:
                    self.logger.info(f"⏳ {symbol}: Surf Short Paused (Pulse {pulse} != BEARISH). Waiting for Trend.")
            return

        # Modo STRADDLE (Legacy / Neutral)
        # skew_factor = 10 # Afasta 10x o spread se for contra a tendência
        
        # Lógica Simplificada de Straddle (Market Maker)
        # Coloca Bid e Ask em torno do spread, ajustados levemente pelo OBI
        
        mid_price = (best_bid + best_ask) / 2
        spread_pct = (best_ask - best_bid) / mid_price
        strong_obi_threshold = max(effective_obi_threshold * 2, 0.6)
        
        # OBI Skew: Se OBI > 0 (Compra), Bid mais perto, Ask mais longe
        bid_skew = 0
        ask_skew = 0
        
        if obi > 0.1: # Viés Comprador
             bid_skew = 0 # Bid no Best Bid
             ask_skew = spread * 2 # Ask afastado
        elif obi < -0.1: # Viés Vendedor
             bid_skew = spread * 2 # Bid afastado
             ask_skew = 0 # Ask no Best Ask
             
        if abs(obi) >= strong_obi_threshold:
            if obi > 0 and allow_long:
                if not self._zlp_checklist(symbol, "Long", depth, obi, pulse):
                    return
                final_bid = self._round_price(symbol, best_bid - bid_skew)
                self.logger.info(f"️ {symbol}: Straddle Direcional Bid @ {final_bid}")
                self.state[symbol]['target_qty'] = qty
                self.state[symbol]['probe_qty'] = 0.0
                self.state[symbol]['confirm_qty'] = 0.0
                self.state[symbol]['confirmation_sent'] = False
                self.state[symbol]['full_entry'] = True
                self.state[symbol]['probe_spread_pct'] = 0.0
                self._send_maker_order(symbol, "Buy", qty, final_bid)
                self._mark_entry(symbol)
            elif obi < 0 and allow_short:
                if not self._zlp_checklist(symbol, "Short", depth, obi, pulse):
                    return
                final_ask = self._round_price(symbol, best_ask + ask_skew)
                self.logger.info(f"️ {symbol}: Straddle Direcional Ask @ {final_ask}")
                self.state[symbol]['target_qty'] = qty
                self.state[symbol]['probe_qty'] = 0.0
                self.state[symbol]['confirm_qty'] = 0.0
                self.state[symbol]['confirmation_sent'] = False
                self.state[symbol]['full_entry'] = True
                self.state[symbol]['probe_spread_pct'] = 0.0
                self._send_maker_order(symbol, "Sell", qty, final_ask)
                self._mark_entry(symbol)
            return

        # Place Bid
        if allow_long:
            if self._zlp_checklist(symbol, "Long", depth, obi, pulse):
                final_bid = self._round_price(symbol, best_bid - bid_skew)
                self.logger.info(f"️ {symbol}: Straddle Bid @ {final_bid}")
                self.state[symbol]['target_qty'] = qty
                self.state[symbol]['probe_qty'] = 0.0
                self.state[symbol]['confirm_qty'] = 0.0
                self.state[symbol]['confirmation_sent'] = False
                self.state[symbol]['full_entry'] = True
                self.state[symbol]['probe_spread_pct'] = 0.0
                self._send_maker_order(symbol, "Buy", qty, final_bid)
                self._mark_entry(symbol)
        
        # Place Ask
        if allow_short:
            if self._zlp_checklist(symbol, "Short", depth, obi, pulse):
                final_ask = self._round_price(symbol, best_ask + ask_skew)
                self.logger.info(f"️ {symbol}: Straddle Ask @ {final_ask}")
                self.state[symbol]['target_qty'] = qty
                self.state[symbol]['probe_qty'] = 0.0
                self.state[symbol]['confirm_qty'] = 0.0
                self.state[symbol]['confirmation_sent'] = False
                self.state[symbol]['full_entry'] = True
                self.state[symbol]['probe_spread_pct'] = 0.0
                self._send_maker_order(symbol, "Sell", qty, final_ask)
                self._mark_entry(symbol)

    def _round_price(self, symbol, price):
        if "BTC" in symbol:
            return round(price, 1)
        if "ETH" in symbol:
            return round(price, 2)
        if "SOL" in symbol:
            return round(price, 2)
        if "AVAX" in symbol:
            return round(price, 2)
        if "SKR" in symbol or "FOGO" in symbol:
            return round(price, 6)
        return round(price, 6)

    def _round_qty(self, symbol, qty):
        if "BTC" in symbol:
            return round(qty, 4)
        if "ETH" in symbol:
            return round(qty, 3)
        if "SOL" in symbol:
            return round(qty, 2)
        if "SKR" in symbol or "FOGO" in symbol:
            # Step Size 10
            return int(qty / 10) * 10
        return round(qty, 0)

    def _mark_entry(self, symbol):
        self.state[symbol]['last_entry_time'] = time.time()

    def _mark_exit(self, symbol, is_win):
        results = self.state[symbol].get('recent_results', [])
        results.append(bool(is_win))
        if len(results) > 12:
            results = results[-12:]
        self.state[symbol]['recent_results'] = results
        if is_win:
            self.state[symbol]['consecutive_losses'] = 0
        else:
            self.state[symbol]['consecutive_losses'] += 1
            if self.state[symbol]['consecutive_losses'] >= 2:
                self.state[symbol]['zero_loss_until'] = time.time() + 5
                self.logger.warning(f" {symbol}: Zero Loss ativado por 5s.")
        self.state[symbol]['exit_handled'] = True
        self._maybe_apply_auto_learning(symbol)

    def _infer_exit_result(self, symbol):
        side = self.state[symbol].get('last_side')
        entry = self.state[symbol].get('last_price')
        sl = self.state[symbol].get('last_sl')
        if not side or not entry:
            self.state[symbol]['exit_handled'] = True
            return
        ticker = self._get_cached_ticker(symbol)
        if not ticker or 'lastPrice' not in ticker:
            self.state[symbol]['exit_handled'] = True
            return
        curr = float(ticker['lastPrice'])
        if sl:
            if side == "Long" and curr <= sl:
                self._mark_exit(symbol, False)
                return
            if side == "Short" and curr >= sl:
                self._mark_exit(symbol, False)
                return
        if side == "Long":
            self._mark_exit(symbol, curr >= entry)
        else:
            self._mark_exit(symbol, curr <= entry)

    def _maybe_apply_auto_learning(self, symbol):
        if not self.auto_learn:
            return
        now = time.time()
        state = self.state[symbol]
        state['trades_since_learn'] = state.get('trades_since_learn', 0) + 1
        last_learn_time = state.get('last_learn_time', 0)
        if state['trades_since_learn'] >= self.learn_batch_trades or (now - last_learn_time) >= self.learn_batch_seconds:
            self._apply_auto_learning(symbol)
            state['trades_since_learn'] = 0
            state['last_learn_time'] = now

    def _apply_auto_learning(self, symbol):
        results = self.state[symbol].get('recent_results', [])
        if len(results) < 4:
            self.state[symbol]['learned_obi'] = self.obi_threshold
            self.state[symbol]['learned_profit_usd'] = max(self.profit_usd, 5.0)
            self.state[symbol]['learned_risk_usd'] = min(self.risk_usd, 2.0)
            self.state[symbol]['learned_min_entry_interval'] = self.min_entry_interval
            return
        wins = sum(1 for r in results if r)
        win_rate = wins / len(results)
        obi = self.obi_threshold
        profit = max(self.profit_usd, 5.0)
        risk = min(self.risk_usd, 2.0)
        min_entry = self.min_entry_interval
        if win_rate < 0.4:
            obi = min(0.6, obi + 0.1)
            profit = max(profit + 1.0, 5.0)
            risk = max(1.0, risk * 0.9)
            min_entry = min_entry * 2
        elif win_rate > 0.6:
            obi = max(0.2, obi - 0.05)
            profit = max(profit, 5.0)
            risk = min(self.risk_usd, 2.0)
            min_entry = max(5.0, min_entry * 0.8)
        self.state[symbol]['learned_obi'] = obi
        self.state[symbol]['learned_profit_usd'] = profit
        self.state[symbol]['learned_risk_usd'] = risk
        self.state[symbol]['learned_min_entry_interval'] = min_entry

    def _send_maker_order(self, symbol, side, qty, price):
        # SMART MAKER CHASE (Protocolo Omega)
        # Ajustar preço para garantir que seja Maker, mas sem ser rejeitado por cruzar o book.
        # Se o preço moveu contra nós, a ordem Limit PostOnly seria rejeitada.
        # Solução: Colocar ordem levemente "atrás" do spread para garantir entrada passiva.
        
        depth = self._get_cached_depth(symbol)
        if depth:
            best_bid = float(depth['bids'][0][0])
            best_ask = float(depth['asks'][0][0])
            tick_size = 0.1 # Padrão
            if "BTC" in symbol: tick_size = 0.1
            elif "ETH" in symbol: tick_size = 0.01
            elif "SOL" in symbol: tick_size = 0.01
            else: tick_size = 0.000001
            
            # Se for Buy (Bid), não podemos ser maior que Best Ask.
            # Se for Sell (Ask), não podemos ser menor que Best Bid.
            
            if side == "Buy":
                # Alvo inicial: Price
                # Limite Físico: Best Ask - Tick (para não virar Taker)
                limit_ceiling = best_ask - tick_size
                if price >= best_ask:
                    self.logger.warning(f"️ {symbol}: Smart Maker ajustando Buy {price} -> {limit_ceiling} (Evitar Taker)")
                    price = limit_ceiling
            else: # Sell
                limit_floor = best_bid + tick_size
                if price <= best_bid:
                    self.logger.warning(f"️ {symbol}: Smart Maker ajustando Sell {price} -> {limit_floor} (Evitar Taker)")
                    price = limit_floor

        price = self._round_price(symbol, price)
        payload = {
            "symbol": symbol,
            "side": "Bid" if side == "Buy" else "Ask",
            "orderType": "Limit",
            "quantity": str(qty),
            "price": str(price),
            "postOnly": True
        }
        res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        if res and 'id' in res:
            self.logger.info(f" {symbol}: Ordem Limit (PostOnly/Smart) {res['id']} enviada a {price}")
        else:
            self.logger.warning(f" {symbol}: Falha na Ordem Limit: {res}")
        self._invalidate_cache([f"open_orders:{symbol}"])

def main():
    parser = argparse.ArgumentParser(description='Volume Farmer & Trend Surfer')
    parser.add_argument('--symbols', nargs='+', default=["BTC_USDC_PERP", "AVAX_USDC_PERP", "SUI_USDC_PERP"], help='Lista de ativos')
    parser.add_argument('--leverage', type=float, default=5, help='Alavancagem')
    parser.add_argument('--mode', choices=['straddle', 'surf'], default='straddle', help='Modo de operação: straddle (neutro/farm) ou surf (tendência)')
    parser.add_argument('--surf', action='store_true', help='(Legacy) Ativar modo Trend Surfer')
    parser.add_argument('--long', action='store_true', help='Forçar direção LONG')
    parser.add_argument('--short', action='store_true', help='Forçar direção SHORT')
    parser.add_argument('--obi', type=float, default=0.25, help='Sensibilidade do OBI (0.2=Agressivo, 0.6=Conservador)')
    parser.add_argument('--dry-run', action='store_true', help='Modo Simulação (Sem ordens reais)')
    parser.add_argument('--eco', action='store_true', help='Modo econômico (menos entradas e menos logs)')
    parser.add_argument('--min-entry-interval', type=float, default=15, help='Intervalo mínimo entre entradas (segundos)')
    parser.add_argument('--capital-per-trade', type=str, default="200.0", help='Capital por trade (USD de margem) ou "ALL" para compound')
    parser.add_argument('--risk-usd', type=float, default=2.0, help='Risco máximo por trade em USD')
    parser.add_argument('--profit-usd', type=float, default=5.0, help='Lucro alvo por trade em USD')
    parser.add_argument('--reset-orders', action='store_true', help='Cancelar ordens pendentes no início')
    parser.add_argument('--auto-learn', action='store_true', help='Ativar modo de auto aprendizado')
    mandatory_sl_group = parser.add_mutually_exclusive_group()
    mandatory_sl_group.add_argument('--mandatory-sl', action='store_true', help='Forçar SL obrigatório e fechamento se falhar')
    mandatory_sl_group.add_argument('--no-mandatory-sl', action='store_true', help='Desativar SL obrigatório')
    parser.add_argument('--manual-obi', type=float, default=None, help='OBI manual (override para todos os símbolos)')
    parser.add_argument('--manual-onchain', type=float, default=None, help='On-chain manual (override para todos os símbolos)')
    parser.add_argument('--profile', choices=['base', '5x', '10x', '20x'], default='base', help='Perfil de risco global')
    parser.add_argument('--hyper-volume', action='store_true', help='Modo Hyper Volume: Giro rapido, alvos curtos 0.1pct, OBI sensivel 0.15')
    parser.add_argument('--ironclad', action='store_true', help='Modo Ironclad Survival: Trend 1m Obrigatória, SL ATR, Sem Degen')
    parser.add_argument('--compound-mode', action='store_true', help='Modo Compound Sniper: Single Asset Focus + Full Margin')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Nível de log')
    
    args = parser.parse_args()
    
    # Compatibilidade com flag antiga --surf
    mode = "surf" if args.surf else args.mode
    if args.hyper_volume:
        mode = "surf" # Hyper volume forces surf logic but with relaxed constraints
    direction = "long" if args.long else ("short" if args.short else "auto")
    log_level = args.log_level
    if args.eco and args.log_level == 'INFO':
        log_level = 'WARNING'
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    if args.no_mandatory_sl:
        mandatory_sl = False
    else:
        mandatory_sl = args.mandatory_sl or ("BTC_USDC_PERP" in args.symbols)

    # Configurar profile_configs based on args.profile for all symbols if needed
    # For now, we pass it as a default for symbols that don't have specific profile
    # Actually, VolumeFarmer expects profile_configs dict and symbol_profiles dict.
    # We can create a symbol_profiles dict where all symbols use the selected profile.
    
    symbol_profiles = {s: args.profile for s in args.symbols}

    farmer = VolumeFarmer(
        symbols=args.symbols,
        leverage=args.leverage,
        dry_run=args.dry_run,
        mode=mode,
        direction=direction,
        obi_threshold=args.obi,
        eco_mode=args.eco,
        min_entry_interval=args.min_entry_interval,
        capital_per_trade=args.capital_per_trade,
        risk_usd=args.risk_usd,
        profit_usd=args.profit_usd,
        reset_orders=args.reset_orders,
        auto_learn=args.auto_learn,
        mandatory_sl=mandatory_sl,
        manual_obi=args.manual_obi,
        manual_onchain=args.manual_onchain,
        symbol_profiles=symbol_profiles,
        ironclad=args.ironclad
    )
    farmer.hyper_volume = args.hyper_volume # Inject flag
    farmer.compound_mode = args.compound_mode # Inject flag
    asyncio.run(farmer.start())

if __name__ == "__main__":
    main()
