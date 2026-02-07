import os
import sys
import time
import math
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backend_analytics import BackpackAnalytics
from advanced_indicators import AdvancedIndicators
from backpack_indicators import BackpackIndicators

# Import New Agents
from agents.macro_oracle import MacroOracle
from agents.liquidity_scout import LiquidityScout
from agents.yield_harvester import YieldHarvester
from agents.security_guardian import SecurityGuardian
from agents.exhaustion_sniper import ExhaustionSniper

from risk_engine import RiskEngine

from profit_tracker import ProfitTracker

class SniperCommander:
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv("BACKPACK_API_KEY"), os.getenv("BACKPACK_API_SECRET"))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.analytics = BackpackAnalytics(self.data)
        self.adv_indicators = AdvancedIndicators(self.data)
        self.indicators = BackpackIndicators()
        self.risk_engine = RiskEngine()
        self.tracker = ProfitTracker() # Init Ledger
        self.BLACKLIST = ["kBONK_USDC_PERP", "ZEREBRO_USDC_PERP", "LIT_USDC_PERP", "OG_USDC_PERP"]
        
        # Initialize Agents
        self.oracle = MacroOracle()
        self.scout = LiquidityScout(self.data)
        self.harvester = YieldHarvester(self.data)
        self.guardian = SecurityGuardian(self.data)
        self.night_owl = ExhaustionSniper(self.data)
        
    def fire_sniper_shot(self, capital_usd=None, target_symbol=None):
        """
        Executes a single high-quality trade with available capital using Multi-Agent Intelligence.
        """
        print("\n COMMANDER: INITIATING MULTI-AGENT SNIPER SHOT")
        print("-" * 50)
        
        # --- PHASE 1: INTELLIGENCE GATHERING (AGENTS) ---
        
        # 1. Macro Oracle (Bias)
        macro_report = self.oracle.get_macro_report()
        macro_bias = macro_report['bias']
        restrictions = macro_report['restrictions']
        print(f" Macro Bias: {macro_bias} | Restrictions: {restrictions}")
        
        # 2. Security Guardian (Health)
        security_report = self.guardian.audit_system()
        if not security_report['approved']:
            print(f"️ Guardian Block: {security_report['reason']}")
            return False
            
        # 3. Determine Capital
        effective_budget = self.tracker.get_effective_budget()
        print(f" EFFECTIVE GLOBAL BUDGET: ${effective_budget:.2f}")
        
        if capital_usd is None:
            bals = self.data.get_balances()
            usdc_avail = bals.get('USDC', {}).get('available', 0)
            capital_usd = min(usdc_avail, effective_budget)
            
        print(f" Ammo Available: ${capital_usd:.2f}")
        if capital_usd < 10:
            print(" Insufficient Ammo (< $10). Aborting.")
            return False

        # --- PHASE 2: TARGET ACQUISITION ---
        
        candidates_df = pd.DataFrame()
        
        if target_symbol:
             print(f" Evaluating Designated Target: {target_symbol}")
             # ... (existing fallback logic for single target) ...
             # We can reuse analytics logic here or simplify
             ticker = self.data.get_ticker(target_symbol)
             if ticker:
                 candidates_df = pd.DataFrame([{
                     'symbol': target_symbol,
                     'price': float(ticker.get('lastPrice', 0)),
                     'funding_rate': float(ticker.get('fundingRate', 0)),
                     'confluence_score': 5,
                     'volatility_24h': 5.0
                 }])
        else:
            # Harvester & Analytics Hybrid
            print(" Agents Scanning for Opportunities...")
            
            # A. Yield Candidates
            yield_opps = self.harvester.harvest_yields(min_apr=10)
            yield_symbols = [x['symbol'] for x in yield_opps]
            
            # B. Momentum Candidates (Analytics)
            momentum_df = self.analytics.get_top_opportunities(limit=10)
            
            # Combine
            # Convert yield_opps to DF format if not empty
            if yield_opps:
                yield_df = pd.DataFrame(yield_opps)
                # Normalize columns to match momentum_df
                # momentum_df has: symbol, price, funding_rate, confluence_score...
                # yield_df has: symbol, funding_rate...
                # We need to fetch price for yield_df if missing
                pass # For simplicity, let's rely on momentum_df which scans all, 
                     # but boost scores for yield_symbols.
            
            candidates_df = momentum_df

        # --- PHASE 3: SELECTION & VALIDATION ---
        
        best_target = None
        best_score = -999
        
        if candidates_df.empty:
            print(" No candidates found.")
            return False

        for idx, row in candidates_df.iterrows():
            symbol = row['symbol']
            if symbol in self.BLACKLIST: continue
            
            # 1. Guardian Check (Pool Health)
            pool_check = self.guardian.audit_system(symbol)
            if not pool_check['approved']:
                # print(f"   ️ Pool Issue {symbol}: {pool_check['reason']}")
                continue
                
            # 2. Macro Check (Bias)
            funding = float(row.get('funding_rate', 0))
            is_long = False
            is_short = False
            
            # Determine proposed direction
            # Yield Logic: Negative Funding -> Long. Positive -> Short.
            if funding < -0.0005: # Paying Longs
                is_long = True
            elif funding > 0.0005: # Paying Shorts
                is_short = True
            else:
                # Momentum Logic
                trend = row.get('trend', 'NEUTRAL')
                if trend == "BULLISH": is_long = True
                elif trend == "BEARISH": is_short = True
                
            # Apply Macro Restrictions
            if is_long and "BLOCK_LONG" in restrictions:
                # print(f"    Macro Blocks Long on {symbol}")
                continue
            if is_short and "BLOCK_SHORT" in restrictions:
                # print(f"    Macro Blocks Short on {symbol}")
                continue
                
            if not is_long and not is_short:
                continue # No clear direction

            # 3. Night Owl Check (Exhaustion)
            # Only run if we need a technical trigger
            owl_signal = self.night_owl.hunt(symbol)
            technical_score = 0
            if owl_signal:
                if is_long and owl_signal['signal'] == "REVERSAL_LONG":
                    technical_score += 5
                elif is_short and owl_signal['signal'] == "REVERSAL_SHORT":
                    technical_score += 5
            
            # 4. Scout Check (Liquidity Walls)
            # Find entry/exit points
            current_price = row.get('price', 0)
            side = 'ask' if is_short else 'bid' # We enter as Maker?
            
            # --- PROTOCOL AEGIS: PRE-FLIGHT CHECK ---
            # Fetch Klines for Confluence Check
            klines = self.data.get_klines(symbol, "1h", limit=300)
            if klines:
                df = pd.DataFrame(klines)
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                # Check Confluences
                check_side = "Bid" if is_long else "Ask"
                passed, reason = self.check_confluences(df, check_side)
                
                if not passed:
                    # print(f"   ️ Aegis Block {symbol}: {reason}")
                    continue
                else:
                    print(f"    Aegis Approved {symbol}: {reason}")
                    technical_score += 10 # Bonus for passing Aegis
            # ----------------------------------------
            
            scout_data = self.scout.find_liquidity_walls(symbol, current_price, side='ask' if is_long else 'bid')
            smart_exit = scout_data['smart_exit_price'] if scout_data else 0
            
            # Scoring
            score = row.get('confluence_score', 0) + technical_score
            
            if score > best_score:
                best_score = score
                best_target = {
                    'symbol': symbol,
                    'side': 'Bid' if is_long else 'Ask',
                    'price': current_price,
                    'smart_exit': smart_exit,
                    'score': score,
                    'volatility': row.get('volatility_24h', 5.0),
                    'leverage': 0, # To be calc
                    'is_yield': (funding < -0.0005), # Only flag as Yield if Negative Funding (Long) for now
                    'funding': funding
                }

        if not best_target:
            print(" No valid targets after Agent Filtering.")
            return False

        # --- PHASE 4: EXECUTION ---
        symbol = best_target['symbol']
        side = best_target['side']
        print(f" COMMANDER: ENGAGING {symbol} ({side})")
        
        # Risk Engine
        leverage = self.risk_engine.calculate_dynamic_leverage(
            symbol, best_target['score'], best_target['volatility'], best_target['funding']
        )
        print(f"   ️ Leverage: {leverage}x")
        
        alloc_size, safe_sl_pct = self.risk_engine.calculate_position_size_usd(
            capital_usd, leverage, best_target['volatility']
        )
        
        if alloc_size > capital_usd: alloc_size = capital_usd
        
        # Set Leverage
        self.trade.set_leverage(symbol, leverage)
        
        # Place Order (Maker)
        qty = (alloc_size * leverage) / best_target['price']
        
        # Adjust Qty precision... (existing logic)
        filters = self.data.get_market_filters(symbol)
        step_size = filters.get('stepSize', 1.0)
        if step_size < 1:
            precision = int(round(-math.log10(step_size), 0))
            qty = round(qty, precision)
        else:
            qty = int(qty // step_size) * step_size
            
        print(f" FIRING: {side} {qty} {symbol}")
        
        
        # USE LIMIT ORDER IF POSSIBLE (MAKER)
        
        # USE LIMIT ORDER IF POSSIBLE (MAKER)
        # Try to place limit at current price (Post Only might reject if crossing, so use standard Limit)
        # To save fees, we want to be Maker, but Sniper needs fill.
        # Compromise: Limit at Bid (for Long) or Ask (for Short) and wait 5s?
        # Or Limit at Market Price (Taker but safer than Market due to slippage protection)
        
        # Strategy: "Smart Taker" - Limit at Ask (Buy) or Bid (Sell)
        # This pays Taker fee but avoids slippage.
        
        limit_price = price
        print(f"   ️  Using LIMIT Order @ {limit_price} (PostOnly) to avoid fees.")
        
        # Retry Logic for PostOnly
        # If rejected (because it crosses the book), we adjust price and retry or fail.
        # Since we want to be Maker, we should place at Bid (for Long) or Ask (for Short).
        # But if we want immediate fill, we might need to be Taker if the market moves away.
        # However, User Instruction says: "Maker-only execution with postOnly=True"
        
        # Adjust price to be slightly passive if we want to ensure PostOnly works without rejection?
        # Or place at market and hope? No, PostOnly rejects if it takes.
        # So for Long, price must be <= Best Bid.
        # For Short, price must be >= Best Ask.
        
        # Let's try to get the current book to be precise.
        ticker = self.data.get_ticker(symbol)
        best_bid = float(ticker.get('bestBid', price))
        best_ask = float(ticker.get('bestAsk', price))
        
        if side == "Bid":
            # Long: Place at Best Bid (Join the Bid)
            limit_price = best_bid
        else:
            # Short: Place at Best Ask (Join the Ask)
            limit_price = best_ask
            
        print(f"    Placing Maker Order at {limit_price} (Side: {side})")

        res = self.trade.execute_order(symbol, side, price=limit_price, quantity=qty, order_type="Limit", post_only=True)
        
        if not res:
            print("   ️  PostOnly Order Rejected (Likely Crossed). Retrying with slight adjustment...")
            # Retry once with slightly better price (more passive)
            if side == "Bid":
                limit_price = best_bid * 0.9995 # 5bps lower
            else:
                limit_price = best_ask * 1.0005 # 5bps higher
                
            print(f"    Retrying Maker Order at {limit_price}...")
            # Ensure price precision before retry
            filters = self.data.get_market_filters(symbol)
            tick_size = filters.get('tickSize', 0.01)
            if tick_size < 1:
                decimals = int(round(-math.log10(tick_size), 0))
                limit_price = round(limit_price, decimals)
            else:
                limit_price = round(limit_price, 0)
                
            res = self.trade.execute_order(symbol, side, price=limit_price, quantity=qty, order_type="Limit", post_only=True)
        
        if res:
            print(f" IMPACT CONFIRMED. Order ID: {res.get('id')}")
            
            # Place Protection (Using Calculated Safe SL)
            self._place_protection(symbol, side, price, qty, leverage, best_target['is_yield'], filters, safe_sl_pct)
            return True
        else:
            print(" Misfire (Execution Failed).")
            return False

    def _place_protection(self, symbol, side, entry_price, quantity, leverage, is_yield, filters, sl_pct_distance=0.015):
        print("️ Deploying Counter-Measures (TP/SL)...")
        time.sleep(1)
        
        # Config
        # IRON RULE: SL 1.5% | TP 5-7%
        tp_roi = 0.06 * leverage # Target 6% ROI
        sl_roi = sl_pct_distance * leverage # Exact match with Risk Engine Calculation
            
        price_move_tp = tp_roi / leverage
        price_move_sl = sl_roi / leverage # This should equal sl_pct_distance
        
        # Validation: Ensure SL price is mathematically correct relative to entry
        # If Long: SL = Entry * (1 - 0.015)
        # If Short: SL = Entry * (1 + 0.015)
        
        if side == "Bid":
            tp_price = entry_price * (1 + price_move_tp)
            sl_price = entry_price * (1 - price_move_sl)
            exit_side = "Ask"
        else:
            tp_price = entry_price * (1 - price_move_tp)
            sl_price = entry_price * (1 + price_move_sl)
            exit_side = "Bid"
            
        # Rounding
        tick_size = filters.get('tickSize', 0.01)
        if tick_size < 1:
            decimals = int(round(-math.log10(tick_size), 0))
            tp_price = round(tp_price, decimals)
            sl_price = round(sl_price, decimals)
        else:
            tp_price = round(tp_price, 0)
            sl_price = round(sl_price, 0)
            
        # Execute
        self.trade.execute_order(symbol, exit_side, price=None, quantity=quantity, 
                                order_type="Market", reduce_only=True, trigger_price=tp_price)
        self.trade.execute_order(symbol, exit_side, price=None, quantity=quantity, 
                                order_type="Market", reduce_only=True, trigger_price=sl_price)
                                
        print(f" Perimeter Secured. SL @ {sl_price} (-{sl_roi*100:.1f}% ROI)")

if __name__ == "__main__":
    commander = SniperCommander()
    commander.fire_sniper_shot()
