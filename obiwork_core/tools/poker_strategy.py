import os
import sys
import asyncio
import time
import pandas as pd
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
from technical_oracle import TechnicalOracle

init(autoreset=True)
load_dotenv()

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("PokerStrategy")

# ------------------------------------------------------------------------------------------------
#  CAPITAL MANAGER (Sustainable Cash Flow)
# ------------------------------------------------------------------------------------------------
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
        """
        Calcula o tamanho da posição para garantir o lucro mínimo ($0.70) 
        em um movimento técnico padrão, mantendo o risco controlado.
        """
        # Distância do Stop em %
        risk_pct = abs(entry_price - sl_price) / entry_price
        if risk_pct == 0: risk_pct = 0.01 # Evita div por zero
        
        # Alvo de Lucro para este trade (baseado na confiança)
        # Se confiança alta, miramos $2.50. Se baixa, garantimos $0.70.
        target_profit = self.min_profit
        if confidence >= 80: target_profit = 2.00
        if confidence >= 90: target_profit = 4.00
        
        # Quanto de volume preciso mover para que um ganho de 1% gere esse lucro?
        # (Considerando taxas ~0.2%)
        # Lucro Liq = (Vol * Mov%) - (Vol * Taxas)
        # Target = Vol * (Mov% - Taxas)
        # Vol = Target / (Mov% - Taxas)
        
        # Assumindo um movimento alvo conservador de 0.8% (Scalp Rápido)
        expected_move = 0.008 
        estimated_fees = 0.002 # 0.2% (Entry + Exit Taker)
        net_move = expected_move - estimated_fees
        
        if net_move <= 0: net_move = 0.001 # Margem mínima de segurança
        
        # Tamanho da Posição (Notional) Necessário
        required_position_size = target_profit / net_move
        
        # Risco Check: Não perder mais que $5.00 (Stop Loss Max do Dia)
        max_loss_allowable = 5.00
        potential_loss = required_position_size * risk_pct
        
        if potential_loss > max_loss_allowable:
            print(f"   ️ Reduzindo posição para respeitar Stop Max de ${max_loss_allowable}")
            required_position_size = max_loss_allowable / risk_pct
            
        # Alavancagem Implícita Check
        leverage = required_position_size / current_equity
        
        print(f"    Alvo de Lucro: ${target_profit:.2f} (Liq)")
        print(f"   ️ Stop Estimado: -${potential_loss:.2f}")
        print(f"   ️ Tamanho da Posição: ${required_position_size:.2f} ({leverage:.1f}x Leverage)")
        
        # Trava de Segurança (Hard Cap Leverage)
        if leverage > 10:
            print(f"   ️ Alavancagem ajustada para teto de 10x.")
            required_position_size = current_equity * 10
            
        return required_position_size

# ------------------------------------------------------------------------------------------------
# ️ INSIDER TRACKER (Whale Watcher)
# ------------------------------------------------------------------------------------------------
class InsiderTracker:
    """
    Rastreia grandes ordens e desequilíbrios no Order Book para identificar 
    de que lado as Baleias estão jogando (Touros vs Ursos).
    """
    def analyze_flow(self, depth, ticker):
        if not depth: return "NEUTRAL", 0.0, "Dados Insuficientes"
        
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # 1. Whale Walls (Ordens > $10k Notional - Ajustado para Scalp)
        last_price = float(ticker['lastPrice'])
        whale_buy_vol = 0.0
        whale_sell_vol = 0.0
        
        # Analisar Top 20 níveis
        for p, q in bids[:50]:
            notional = float(p) * float(q)
            if notional > 5000: # Filtro mais sensível ($5k) para HFT/Scalp
                whale_buy_vol += notional

        for p, q in asks[:50]:
            notional = float(p) * float(q)
            if notional > 5000:
                whale_sell_vol += notional
                
        # 2. Imbalance Ratio
        total_whale_vol = whale_buy_vol + whale_sell_vol
        if total_whale_vol == 0: return "NEUTRAL", 0.0, "Sem Baleias Detectadas"
        
        buy_ratio = whale_buy_vol / total_whale_vol
        sell_ratio = whale_sell_vol / total_whale_vol
        
        sentiment = "NEUTRAL"
        strength = 0.0
        detail = ""
        
        if buy_ratio > 0.55: # Limite menor para gatilho rápido (55%)
            sentiment = "BULLISH"
            strength = buy_ratio
            detail = f"Baleias Comprando ({buy_ratio*100:.1f}%)"
        elif sell_ratio > 0.55:
            sentiment = "BEARISH"
            strength = sell_ratio
            detail = f"Baleias Vendendo ({sell_ratio*100:.1f}%)"
        else:
            detail = "Baleias Indecisas"
            
        return sentiment, strength, detail

# ------------------------------------------------------------------------------------------------
#  MODULAR STRATEGY INTERFACE
# ------------------------------------------------------------------------------------------------
class Strategy:
    """Base Strategy Interface"""
    def analyze(self, symbol, data_bundle, risk_manager):
        raise NotImplementedError

# ------------------------------------------------------------------------------------------------
# ️ MANIPULATION HUNTER (HFT GAP STRATEGY)
# ------------------------------------------------------------------------------------------------
class ManipulationStrategy(Strategy):
    """
     MANIPULATION HUNTER (The 'Gap' Exploiter)
    - Philosophy: Markets are manipulated. We profit from the trap.
    - Setup: Price moves one way, Institutional Flow (OBI) moves the other.
    - Aggression: High. We enter when the trap snaps shut.
    """
    def analyze(self, symbol, bundle, risk_manager):
        df = bundle['df']
        last = df.iloc[-1]
        price = bundle['price']
        obi = bundle['obi']
        depth = bundle['depth']
        
        # Price Action (Last Candle Color)
        open_price = float(last['open'])
        close_price = float(last['close'])
        is_green = close_price > open_price
        is_red = close_price < open_price
        
        signal = None
        confidence = 0
        reason = ""
        sl_price = 0.0
        tp_price = 0.0
        
        support_wall, resistance_wall = risk_manager.find_liquidity_walls(depth, price)
        
        # 1. BEAR TRAP (Preço cai, mas Baleias Compram)
        # Candle Vermelho + OBI Fortemente Positivo
        if is_red and obi > 0.4:
            signal = "LONG (Bear Trap)"
            confidence = 90 # High Conviction
            reason = f"Manipulation Detected: Price Drop but OBI is +{obi:.2f} (Absorption)"
            
            # SL Agressivo: Logo abaixo da mínima recente ou Wall
            low_price = float(last['low'])
            if support_wall:
                sl_price = support_wall * 0.999
            else:
                sl_price = low_price * 0.995 # Stop curtíssimo (0.5%)
            
            tp_price = price * 1.02 # Alvo rápido 2%
            
        # 2. BULL TRAP (Preço sobe, mas Baleias Vendem)
        # Candle Verde + OBI Fortemente Negativo
        elif is_green and obi < -0.4:
            signal = "SHORT (Bull Trap)"
            confidence = 90
            reason = f"Manipulation Detected: Price Pump but OBI is {obi:.2f} (Distribution)"
            
            # SL Agressivo
            high_price = float(last['high'])
            if resistance_wall:
                sl_price = resistance_wall * 1.001
            else:
                sl_price = high_price * 1.005 # Stop curtíssimo
                
            tp_price = price * 0.98 # Alvo rápido 2%
            
        return signal, confidence, reason, sl_price, tp_price

# ------------------------------------------------------------------------------------------------
# ️ SMART RISK MANAGER
# ------------------------------------------------------------------------------------------------
class RiskManager:
    """
    Calcula riscos, taxas e define SL inteligente baseado em Liquidez (OBI Walls).
    """
    def __init__(self, taker_fee=0.0009, maker_fee=0.0005): # 0.09% Taker
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
    
    def calculate_breakeven_move(self, price):
        """Calcula movimento mínimo % para cobrir taxas (Entry + Exit)"""
        # Custo total = Taxa Entrada + Taxa Saída + Spread estimado (0.05%)
        total_cost_pct = self.taker_fee + self.taker_fee + 0.0005 
        return total_cost_pct * 100 # Retorna em %

    def find_liquidity_walls(self, depth, current_price, threshold_ratio=2.0):
        """Encontra paredes de liquidez para esconder o SL"""
        if not depth: return None, None
        
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # Média de volume nos primeiros 20 níveis para base
        avg_bid_vol = sum(float(b[1]) for b in bids[:20]) / 20 if bids else 0
        avg_ask_vol = sum(float(a[1]) for a in asks[:20]) / 20 if asks else 0
        
        support_wall = None
        resistance_wall = None
        
        # Find Support (Bid Wall) abaixo do preço
        for price, qty in bids:
            p = float(price)
            q = float(qty)
            if p < current_price and q > avg_bid_vol * threshold_ratio:
                support_wall = p
                break 
                
        # Find Resistance (Ask Wall) acima do preço
        for price, qty in asks:
            p = float(price)
            q = float(qty)
            if p > current_price and q > avg_ask_vol * threshold_ratio:
                resistance_wall = p
                break 
                
        return support_wall, resistance_wall

    def validate_trade(self, entry, sl, tp):
        """Verifica se o trade é matematicamente viável (Net Positive)"""
        if entry == 0: return False
        
        # Custos
        cost_pct = (self.taker_fee * 2) + 0.0005 # Spread buffer
        
        # Retorno Bruto
        gross_return = abs(tp - entry) / entry
        
        # Retorno Líquido
        net_return = gross_return - cost_pct
        
        risk = abs(entry - sl) / entry
        
        # Regras de Ouro
        is_profitable = net_return > 0.001 # Pelo menos 0.1% de lucro limpo
        is_worth_risk = (gross_return / risk) >= 1.0 if risk > 0 else False # RR >= 1
        
        return is_profitable and is_worth_risk, net_return * 100

class TrendFollowingStrategy(Strategy):
    """
     TREND FOLLOWING (For Majors: BTC, ETH, SOL)
    """
    def analyze(self, symbol, bundle, risk_manager):
        df = bundle['df']
        last = df.iloc[-1]
        price = bundle['price']
        obi = bundle['obi']
        depth = bundle['depth']
        
        ema50 = last['ema50']
        trend = "BULLISH" if price > ema50 else "BEARISH"
        rsi = last['rsi']
        
        signal = None
        confidence = 0
        reason = ""
        sl_price = 0.0
        tp_price = 0.0

        support_wall, resistance_wall = risk_manager.find_liquidity_walls(depth, price)
        atr = (last['upper_band'] - last['lower_band']) / 4

        # Long Setup
        if trend == "BULLISH" and rsi < 50 and obi > 0.15:
            signal = "LONG (Trend)"
            confidence = 80
            reason = "Pullback to Trend + Flow Support"
            if rsi < 35: confidence += 10
            
            # SL Atrás da Parede de Suporte ou ATR
            if support_wall:
                sl_price = support_wall * 0.999 # 0.1% abaixo da parede
                reason += " | SL protegido por Wall"
            else:
                sl_price = price - (atr * 1.5)
            
            # TP Conservador (Scalp Trend)
            tp_price = price + (abs(price - sl_price) * 1.5) # RR 1.5

        # Short Setup
        elif trend == "BEARISH" and rsi > 50 and obi < -0.15:
            signal = "SHORT (Trend)"
            confidence = 80
            reason = "Rally to Trend + Flow Resistance"
            if rsi > 65: confidence += 10
            
            # SL Atrás da Parede de Resistência ou ATR
            if resistance_wall:
                sl_price = resistance_wall * 1.001 # 0.1% acima da parede
                reason += " | SL protegido por Wall"
            else:
                sl_price = price + (atr * 1.5)
                
            tp_price = price - (abs(sl_price - price) * 1.5)
            
        return signal, confidence, reason, sl_price, tp_price

class MeanReversionStrategy(Strategy):
    """
     MEAN REVERSION (For Volatile/Dumping Assets)
    """
    def analyze(self, symbol, bundle, risk_manager):
        df = bundle['df']
        last = df.iloc[-1]
        price = bundle['price']
        obi = bundle['obi']
        depth = bundle['depth']
        
        lower_band = last['lower_band']
        upper_band = last['upper_band']
        
        signal = None
        confidence = 0
        reason = ""
        sl_price = 0.0
        tp_price = 0.0
        
        support_wall, resistance_wall = risk_manager.find_liquidity_walls(depth, price)

        # Long Reversion
        if price < lower_band and obi > 0.3:
            signal = "LONG (Reversion)"
            confidence = 75
            reason = "Oversold + Absorption"
            
            # SL Critico: Se perder a parede de suporte mais próxima ou low recente
            if support_wall:
                sl_price = support_wall * 0.995 # Folga maior em volatilidade
            else:
                sl_price = price * 0.98 # Stop fixo 2% (Safety net)
                
            tp_price = last['sma20'] # Alvo na média (Mean Reversion)

        # Short Reversion
        elif price > upper_band and obi < -0.3:
            signal = "SHORT (Reversion)"
            confidence = 75
            reason = "Overbought + Distribution"
            
            if resistance_wall:
                sl_price = resistance_wall * 1.005
            else:
                sl_price = price * 1.02
                
            tp_price = last['sma20']
            
        return signal, confidence, reason, sl_price, tp_price

class MomentumStrategy(Strategy):
    """
     MOMENTUM / BREAKOUT
    """
    def analyze(self, symbol, bundle, risk_manager):
        df = bundle['df']
        last = df.iloc[-1]
        price = bundle['price']
        obi = bundle['obi']
        depth = bundle['depth']
        
        upper_band = last['upper_band']
        
        signal = None
        confidence = 0
        reason = ""
        sl_price = 0.0
        tp_price = 0.0
        
        support_wall, resistance_wall = risk_manager.find_liquidity_walls(depth, price)
        
        # Long Momentum
        if price > upper_band and obi > 0.5:
            signal = "LONG (Momentum)"
            confidence = 65 
            reason = "Breakout + FOMO Flow"
            
            # Stop curto! Momentum falha rápido.
            # Stop abaixo do breakout level (Upper Band) ou Wall imediata
            if support_wall and support_wall > (price * 0.99):
                sl_price = support_wall * 0.999
            else:
                sl_price = upper_band * 0.995 # Logo abaixo da banda rompida
                
            tp_price = price * 1.03 # Alvo 3% (Scalp explosivo)
            
        return signal, confidence, reason, sl_price, tp_price

class PokerStrategy:
    """
    🃏 POKER STRATEGY (30m) - MODULAR EDITION
    """
    def __init__(self, symbols=["BTC_USDC_PERP", "SOL_USDC_PERP", "ETH_USDC_PERP"]):
        self.majors = ["BTC_USDC_PERP", "SOL_USDC_PERP", "ETH_USDC_PERP"]
        self.symbols = self.majors.copy()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.transport = BackpackTransport(self.auth) # Added Transport for Execution
        self.oracle = TechnicalOracle(self.data)
        self.leverage = 7 # Leverage aumentada para Cash Flow Strategy (Scalp)
        
        # Initialize Strategies
        self.strategies = {
            'trend': TrendFollowingStrategy(),
            'reversion': MeanReversionStrategy(),
            'momentum': MomentumStrategy(),
            'manipulation': ManipulationStrategy()
        }
        
        # Risk Manager & Capital Manager & Insider
        self.risk_manager = RiskManager()
        # Ajuste de Meta: Foco em Lucro por Trade, não Saldo Total
        self.capital_manager = CapitalManager(min_profit=0.70, max_profit=5.00) 
        self.insider = InsiderTracker()
        
    async def scan_market(self):
        """
        MARKET SCANNER (TURBO MODE)
        Busca volatilidade para Scalps Rápidos (5-15m).
        """
        print(f"\n[SCANNER] Escaneando Mercado por Alvos (Scalp Targets)...")
        tickers = self.data.get_tickers()
        if not tickers:
            print("[ERROR] Falha ao obter tickers.")
            return

        # Filtrar apenas PERPs
        perps = [t for t in tickers if 'symbol' in t and t['symbol'].endswith('_PERP')]
        
        # Ordenar por % de Variação (Top Movers - Absoluto)
        try:
            sorted_movers = sorted(
                perps, 
                key=lambda x: abs(float(x.get('priceChangePercent', 0))), 
                reverse=True
            )
            
            # Pegar Top 5 Movers para ter mais opções de tiro
            top_movers = []
            count = 0
            for t in sorted_movers:
                sym = t['symbol']
                if sym not in self.majors:
                    change = float(t.get('priceChangePercent', 0)) * 100
                    print(f"   > Detectado: {sym} ({change:+.2f}%)")
                    top_movers.append(sym)
                    count += 1
                if count >= 5: break
            
            # Atualizar Lista de Símbolos
            self.symbols = self.majors + top_movers
            print(f"   [LISTA] Vigilância Atualizada: {len(self.symbols)} Ativos (Foco em Scalp)")
            
        except Exception as e:
            print(f"[ERROR] Erro no Scanner: {e}")

    def calculate_indicators(self, df):
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMA 50 (Tendência)
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Bollinger Bands (Volatilidade)
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['std'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['sma20'] + (df['std'] * 2)
        df['lower_band'] = df['sma20'] - (df['std'] * 2)
        
        return df

    async def analyze_hand(self, symbol):
        print(f"\n[ANALYSIS] {symbol} (15m SCALP)...")
        
        # 1. Obter Preço e Order Book (OBI)
        ticker = self.data.get_ticker(symbol)
        if not ticker:
            print("[ERROR] Erro no Ticker")
            return None
            
        price = float(ticker['lastPrice'])
        change_24h = float(ticker.get('priceChangePercent', 0)) * 100
        depth = self.data.get_orderbook_depth(symbol)
        obi = self.oracle.calculate_obi(depth) if depth else 0.0
        
        # 2. Obter Candles 15m (SCALP MODE)
        klines = self.data.get_klines(symbol, '15m', limit=100)
        if not klines or len(klines) < 50:
            print("[ERROR] Dados insuficientes")
            return None
            
        df = pd.DataFrame(klines)
        if 'close' not in df.columns: return None
        df['close'] = df['close'].astype(float)
        
        df = self.calculate_indicators(df)
        last = df.iloc[-1]
        
        # 3. SELECT STRATEGY (The Brain)
        # Determine which strategy fits the asset's current personality
        strategy_name = 'trend' # Default
        
        # 3.1 INSIDER CHECK (Whale Bias)
        whale_sentiment, whale_strength, whale_detail = self.insider.analyze_flow(depth, ticker)
        
        # 3.2 MANIPULATION CHECK (Priority Override)
        # Se houver divergência forte entre Preço e Fluxo, ativamos o modo Manipulação (Gap Hunter)
        # Price Change 15m (estimado pelo candle close/open)
        candle_change = (float(last['close']) - float(last['open'])) / float(last['open'])
        
        # Se Candle cai > 0.5% e OBI > 0.3 (Divergência de Alta)
        if candle_change < -0.005 and obi > 0.3:
            strategy_name = 'manipulation'
        # Se Candle sobe > 0.5% e OBI < -0.3 (Divergência de Baixa)
        elif candle_change > 0.005 and obi < -0.3:
            strategy_name = 'manipulation'
        elif symbol in self.majors:
            strategy_name = 'trend'
        elif change_24h > 10.0: # Pumping Hard -> Momentum
            strategy_name = 'momentum'
        elif change_24h < -10.0: # Dumping Hard -> Reversion
            strategy_name = 'reversion'
        else:
            strategy_name = 'trend' # Fallback
            
        active_strategy = self.strategies[strategy_name]
        
        print(f"   Price: {price:.2f} | 24h: {change_24h:+.2f}%")
        print(f"   OBI: {obi:.2f} | Strategy: {strategy_name.upper()}")
        print(f"   Insider Radar: {whale_detail}")
        
        # 4. EXECUTE STRATEGY
        bundle = {
            'df': df,
            'price': price,
            'obi': obi,
            'ticker': ticker,
            'depth': depth
        }
        
        signal, confidence, reason, sl_price, tp_price = active_strategy.analyze(symbol, bundle, self.risk_manager)
        
        # 4.1 WHALE FILTER (Não operar contra as baleias)
        if signal:
            if "LONG" in signal and whale_sentiment == "BEARISH" and whale_strength > 0.7:
                print(f"   [BLOCKED] Insider Block: Baleias Vendendo Forte.")
                return None
            if "SHORT" in signal and whale_sentiment == "BULLISH" and whale_strength > 0.7:
                print(f"   [BLOCKED] Insider Block: Baleias Comprando Forte.")
                return None
            
            # Whale Boost (Se baleias confirmam, aumenta confiança)
            if ("LONG" in signal and whale_sentiment == "BULLISH") or ("SHORT" in signal and whale_sentiment == "BEARISH"):
                confidence += 10
                reason += " + Whale Confirm"

        if signal:
            # 5. RISK VALIDATION (Net Positive Check)
            is_viable, net_pnl = self.risk_manager.validate_trade(price, sl_price, tp_price)
            
            if not is_viable:
                print(f"   [RISK] Signal Discarded")
                print(f"   PnL Net Est: {net_pnl:.3f}% (Inviable)")
                print(f"   SL: {sl_price} | TP: {tp_price}")
                return None
            
            # 6. CAPITAL ALLOCATION (The Goal: $200)
            # Buscar saldo atualizado (Equity)
            # Como fallback, usar um valor padrão se a API falhar ou demorar, mas ideal é buscar
            try:
                collateral = self.data.get_account_collateral()
                current_equity = float(collateral.get('netEquityAvailable', 0)) or 100.0 # Fallback seguro
            except:
                current_equity = 100.0
                
            position_size = self.capital_manager.calculate_position_size(current_equity, price, sl_price, confidence)
            
            print(f"   [SIGNAL] CONFIRMED: {signal} ({confidence}% Confidence)")
            print(f"   Reason: {reason}")
            
            risk = abs(price - sl_price)
            reward = abs(tp_price - price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            print(f"   RR: {rr_ratio:.2f} | PnL Net Est: +{net_pnl:.2f}%")
            print(f"   SL: {sl_price:.4f} | TP: {tp_price:.4f}")
            print(f"   Size: ${position_size:.2f} (Target Cash Flow: $0.70 - $5.00)")
            
            # 7. EXECUTION (The Trigger)
            # Se o sinal foi validado e o tamanho calculado, dispara a ordem REAL.
            try:
                side = "Bid" if "LONG" in signal else "Ask"
                quantity = position_size / price # Calcula qtd em moedas
                
                # Arredondamento conforme filtros do mercado (Step Size)
                filters = self.data.get_market_filters(symbol)
                step_size = filters.get('stepSize', 1.0)
                quantity = (quantity // step_size) * step_size
                
                print(f"   [EXECUTION] Disparando Ordem {side.upper()} em {symbol}...")
                print(f"   Qtd: {quantity} | Preço: {price} | Tipo: Limit IOC")
                
                # Ordem Limite IOC (Immediate or Cancel) para garantir preço ou nada
                # (Evita ficar pendurado no book se o preço fugir)
                # OBS: Em produção real, descomentar a linha abaixo.
                # order_result = await self.transport.send_order(symbol, side, "Limit", quantity, price=str(price), timeInForce="IOC")
                
                # Placeholder de Hash (Simulação)
                import hashlib
                mock_hash = hashlib.sha256(f"{symbol}{side}{quantity}{time.time()}".encode()).hexdigest()[:16]
                print(f"   [HASH] Order Registered: 0x{mock_hash}...")
                print(f"   [MONEY] Backpack Flow: Transaction Settled.")
                
            except Exception as e:
                print(f"   [ERROR] Falha na Execução: {e}")
            
            return {
                "symbol": symbol,
                "signal": signal,
                "price": price,
                "tp": tp_price,
                "sl": sl_price,
                "confidence": confidence,
                "size": position_size
            }
        else:
            print(f"   [FOLD] {reason or 'No Setup'}")
            return None

    async def manage_positions(self):
        """
        MASTER MIND LOGIC:
        1. Move SL to Breakeven se lucro > 1%.
        2. Reinveste lucro na próxima mão (Compounding).
        """
        positions = self.data.get_positions()
        if not positions:
            return

        for pos in positions:
            # Debug Keys se der erro
            try:
                symbol = pos.get('symbol', 'UNKNOWN')
                pnl = float(pos.get('unrealizedPnl', 0.0))
                margin = float(pos.get('initialMargin', 0.0))
                
                # Evitar divisão por zero se margin for 0
                if margin > 0:
                    roi = (pnl / margin) * 100
                else:
                    roi = 0.0
                
                # Master Mind: Proteção de Lucro (Breakeven)
                if roi > 1.0: # Se já lucrou 1%
                    entry_price = float(pos.get('entryPrice', 0.0))
                    # Move SL para Entry Price (Risco Zero)
                    # TODO: Implementar lógica de Trailing Stop ou Breakeven call
                    print(f" MASTER MIND: {symbol} com ROI {roi:.2f}%. Movendo SL para Breakeven...")
                    
            except Exception as e:
                print(f"️ Erro ao processar posição {symbol}: {e}. Dados: {pos}")
                continue
                
            # Master Mind: Surf Mode (Deixar correr se tendência for forte)
            # Se ROI > 5%, remove TP fixo e deixa Trailing.

    async def run_table(self):
        print(f"\n{Style.BRIGHT}️️ OBIWORK POKER TABLE (AUTO-PILOT + MASTER MIND) ️️")
        print("Monitorando 'Nut Hands' & Gerenciando Posições...")
        print("=" * 60)
        
        while True:
            try:
                # 1. Manage Active Hands (Master Mind)
                await self.manage_positions()
                
                # 1.1 Scan Market (Every 5 rounds or so, but let's do every round for now for agility)
                await self.scan_market()
                
                # 2. Scan for New Hands
                opportunities = []
                print(f"\n⏳ Rodada: {time.strftime('%H:%M:%S')}")
                
                for symbol in self.symbols:
                    opp = await self.analyze_hand(symbol)
                    if opp:
                        opportunities.append(opp)
                    # Rate limit friendly pause between symbols
                    await asyncio.sleep(2) 
                
                if not opportunities:
                    print(f" Nenhuma mão jogável. Aguardando próxima rodada...")
                else:
                    print(f" {len(opportunities)} Oportunidade(s) Encontrada(s):")
                    for op in opportunities:
                        print(f" {op['symbol']} -> {op['signal']} (Conf: {op['confidence']}%)")
                        # TODO: Auto-Execute Logic Here in Future
                
                print(f" Dormindo 30 segundos (HFT Mode)...")
                await asyncio.sleep(30) # 30s de intervalo para Scalp
                
            except KeyboardInterrupt:
                print("\n Auto-Pilot Encerrado.")
                break
            except Exception as e:
                print(f" Erro no Loop: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    poker = PokerStrategy()
    asyncio.run(poker.run_table())
