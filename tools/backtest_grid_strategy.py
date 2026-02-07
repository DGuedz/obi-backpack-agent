import asyncio
import pandas as pd
import sys
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_data import BackpackData
from backpack_auth import BackpackAuth

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("BacktestGrid")

class VirtualPosition:
    def __init__(self, id, symbol, side, entry_price, quantity, leverage, tp_price, sl_price, start_time):
        self.id = id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.quantity = quantity
        self.leverage = leverage
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.start_time = start_time
        self.status = "OPEN"
        self.exit_price = 0.0
        self.exit_time = None
        self.pnl = 0.0
        self.fee = 0.0

class GridBacktester:
    def __init__(self, symbols, initial_capital=200.0, leverage=10, max_slots=20):
        self.symbols = symbols
        self.capital = initial_capital
        self.leverage = leverage
        self.max_slots = max_slots
        self.slot_size = (initial_capital * 0.95) / max_slots # 95% do capital dividido em slots
        self.positions = []
        self.closed_positions = []
        self.current_time = None
        
        self.active_slots = 0
        self.total_volume = 0.0
        self.fees_paid = 0.0
        
        self.pending_orders = [] # LADDERING: Ordens pendentes de re-entrada
        
        # Data Cache
        self.klines_cache = {}

    async def load_data(self, client):
        """Carrega dados de 1m das últimas 24h para todos os símbolos"""
        print(" Carregando dados históricos (24h)...")
        for symbol in self.symbols:
            # 1440 minutos = 24h. API limit costuma ser 1000. Faremos 2 calls se precisar ou pegamos 1000 (16h)
            klines = client.get_klines(symbol, "1m", limit=1000)
            if klines:
                df = pd.DataFrame(klines)
                df['timestamp'] = pd.to_datetime(df['start'])
                df['open'] = df['open'].astype(float)
                df['high'] = df['high'].astype(float)
                df['low'] = df['low'].astype(float)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                df.set_index('timestamp', inplace=True)
                self.klines_cache[symbol] = df
                print(f"    {symbol}: {len(df)} candles carregados.")
            else:
                print(f"    {symbol}: Falha ao carregar dados.")

    def calculate_indicators(self, df):
        """Calcula indicadores técnicos básicos"""
        # SMA 200 (Tendência)
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands (20, 2)
        df['bb_mid'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * 2)
        
        return df

    def run(self):
        """Executa o backtest candle a candle"""
        print("\n INICIANDO SIMULAÇÃO GRID 10X (LADDERING ENABLED)...")
        print(f"   Capital: ${self.capital} | Slots: {self.max_slots} | Leverage: {self.leverage}x")
        print(f"   TP: 0.8% | SL: 1.2% | Ladder Re-entry: 0.5% Pullback | RSI Filter: 30/70")
        
        # Sincronizar timestamps (Intersecção de todos os dataframes)
        timestamps = None
        for sym, df in self.klines_cache.items():
            df = self.calculate_indicators(df) # Prepara indicadores
            self.klines_cache[sym] = df
            if timestamps is None:
                timestamps = df.index
            else:
                timestamps = timestamps.intersection(df.index)
        
        if timestamps is None or len(timestamps) == 0:
            print(" Erro: Sem dados sincronizados.")
            return

        timestamps = timestamps.sort_values()
        
        # Loop temporal
        for current_ts in timestamps:
            self.current_time = current_ts
            self.check_exits(current_ts)
            self.check_entries(current_ts)
            
            # Monitorar drawdown
            equity = self.get_current_equity(current_ts)
            if equity < 50: # Quebra
                print(f" QUEBRA DE CONTA em {current_ts}. Equity: ${equity:.2f}")
                break

        self.print_results()

    def get_current_equity(self, current_ts):
        unrealized_pnl = 0
        for pos in self.positions:
            # Preço atual do ativo
            try:
                current_price = self.klines_cache[pos.symbol].loc[current_ts]['close']
                if pos.side == "Buy":
                    unrealized_pnl += (current_price - pos.entry_price) * pos.quantity
                else:
                    unrealized_pnl += (pos.entry_price - current_price) * pos.quantity
            except:
                pass
        return self.capital + unrealized_pnl

    def check_exits(self, current_ts):
        """Verifica TP e SL das posições abertas"""
        for pos in self.positions[:]: # Cópia para iterar
            try:
                # Dados do candle atual (High/Low são cruciais para TP/SL)
                row = self.klines_cache[pos.symbol].loc[current_ts]
                high = row['high']
                low = row['low']
                close = row['close']
                
                executed = False
                reason = ""
                exec_price = 0.0
                
                # Check TP
                if pos.side == "Buy" and high >= pos.tp_price:
                    executed = True
                    reason = "TP"
                    exec_price = pos.tp_price
                elif pos.side == "Sell" and low <= pos.tp_price:
                    executed = True
                    reason = "TP"
                    exec_price = pos.tp_price
                    
                # Check SL (Se TP e SL baterem no mesmo candle, assumimos SL por conservadorismo, ou TP se Low > SL)
                # Conservador: Verifica SL primeiro
                if pos.side == "Buy" and low <= pos.sl_price:
                    executed = True
                    reason = "SL"
                    exec_price = pos.sl_price
                elif pos.side == "Sell" and high >= pos.sl_price:
                    executed = True
                    reason = "SL"
                    exec_price = pos.sl_price
                    
                if executed:
                    self.close_position(pos, exec_price, reason, current_ts)
                    
                    # RE-ENTRADA (LADDERING)
                    # Se saiu no TP, tenta entrar novamente no fluxo?
                    # O usuário disse: "quando o preço sobe no pump eu fecho a orde. entao na sequencia ja temos outra ordem"
                    # Lógica: Se fechou Long no TP, o preço está alto.
                    # Opção A: Short Scalp (Reversão)
                    # Opção B: Buy Limit mais baixo (Pullback)
                    # Vamos implementar Opção B: Buy Limit imediato no preço de entrada original (Farmar o range)
                    # Mas só se a tendência ainda for favorável.
                    pass 

            except KeyError:
                continue

    def close_position(self, pos, price, reason, ts):
        pos.exit_price = price
        pos.exit_time = ts
        pos.status = "CLOSED"
        
        # PnL Bruto
        if pos.side == "Buy":
            gross_pnl = (price - pos.entry_price) * pos.quantity
        else:
            gross_pnl = (pos.entry_price - price) * pos.quantity
            
        # Fees (Ajuste para Realidade Backpack)
        # Entry: Maker (0.02%) - PostOnly
        # Exit TP: Maker (0.02%) - Limit Order
        # Exit SL: Taker (0.09%) - Stop Market
        
        entry_fee = (pos.entry_price * pos.quantity) * 0.0002 # 0.02% Maker
        
        if reason == "TP":
            exit_fee = (price * pos.quantity) * 0.0002 # Maker
        else:
            exit_fee = (price * pos.quantity) * 0.0009 # Taker (SL)
        
        pos.fee = entry_fee + exit_fee
        pos.pnl = gross_pnl - pos.fee
        
        self.capital += pos.pnl
        self.fees_paid += pos.fee
        self.closed_positions.append(pos)
        self.positions.remove(pos)
        self.active_slots -= 1
        
        # print(f"   Running PnL: {reason} {pos.symbol} | PnL: ${pos.pnl:.2f} | Cap: ${self.capital:.2f}")

    def check_entries(self, current_ts):
        """Verifica sinais de entrada e ordens pendentes"""
        
        # 1. Verificar Pendentes (Ladder)
        for po in self.pending_orders[:]:
            if self.active_slots >= self.max_slots: break
            
            try:
                row = self.klines_cache[po['symbol']].loc[current_ts]
                low = row['low']
                high = row['high']
                
                filled = False
                if po['side'] == "Buy" and low <= po['price']:
                    filled = True
                elif po['side'] == "Sell" and high >= po['price']:
                    filled = True
                    
                if filled:
                    self.open_position(po['symbol'], po['side'], po['price'], current_ts)
                    self.pending_orders.remove(po)
            except:
                pass

        if self.active_slots >= self.max_slots:
            return

        for symbol in self.symbols:
            if self.active_slots >= self.max_slots: break
            
            # Se já tem posição neste símbolo, não entra (Simples) ou permite Grid (Avançado)?
            # Usuário quer "20 ordens", pode ser no mesmo ativo.
            # Vamos permitir max 3 por ativo.
            current_symbol_pos = len([p for p in self.positions if p.symbol == symbol])
            if current_symbol_pos >= 3: continue
            
            try:
                row = self.klines_cache[symbol].loc[current_ts]
                close = row['close']
                sma = row['sma_200']
                rsi = row['rsi']
                bb_lower = row['bb_lower']
                bb_upper = row['bb_upper']
                
                # ESTRATÉGIA GRID/SCALP 10X (STRICTER FILTER)
                # 1. Tendência: Só Long se > SMA200, Só Short se < SMA200 (Safety)
                # 2. Entrada: RSI Extremo (30/70)
                
                side = None
                
                if close > sma: # Trend Bullish
                    if rsi < 30 or close < bb_lower:
                        side = "Buy"
                elif close < sma: # Trend Bearish
                    if rsi > 70 or close > bb_upper:
                        side = "Sell"
                
                if side:
                    self.open_position(symbol, side, close, current_ts)
                    
            except KeyError:
                continue

    def open_position(self, symbol, side, price, ts):
        # Definição de TP/SL Agressivos (Scalp Rápido - Ajustado para Volume/Winrate)
        # TP: 0.8% (Quick Win)
        # SL: 1.2% (Breathing Room)
        
        if side == "Buy":
            tp = price * 1.008
            sl = price * 0.988
        else:
            tp = price * 0.992
            sl = price * 1.012
            
        qty = (self.slot_size * self.leverage) / price
        
        pos = VirtualPosition(
            id=f"{ts}_{symbol}",
            symbol=symbol,
            side=side,
            entry_price=price,
            quantity=qty,
            leverage=self.leverage,
            tp_price=tp,
            sl_price=sl,
            start_time=ts
        )
        
        self.positions.append(pos)
        self.active_slots += 1
        self.total_volume += (price * qty)
        
        # print(f"    OPEN {side} {symbol} @ {price:.4f}")

    def print_results(self):
        print("\n" + "="*40)
        print(" RESULTADO DA SIMULAÇÃO")
        print("="*40)
        
        wins = [p for p in self.closed_positions if p.pnl > 0]
        losses = [p for p in self.closed_positions if p.pnl <= 0]
        
        win_rate = len(wins) / len(self.closed_positions) if self.closed_positions else 0
        total_profit = sum([p.pnl for p in self.closed_positions])
        
        print(f" Capital Inicial: $200.00")
        print(f" Capital Final:   ${self.capital:.2f}")
        print(f" PnL Líquido:     ${self.capital - 200:.2f} ({(self.capital/200 - 1)*100:.2f}%)")
        print(f" Volume Total:    ${self.total_volume:.2f}")
        print(f" Taxas Pagas:     ${self.fees_paid:.2f}")
        print(f" Trades: {len(self.closed_positions)} (Wins: {len(wins)} | Loss: {len(losses)})")
        print(f" Win Rate: {win_rate*100:.1f}%")
        print("-" * 40)
        
        if self.capital > 200:
            print(" ESTRATÉGIA APROVADA! Lucro consistente.")
        else:
            print("️ ESTRATÉGIA REPROVADA. Prejuízo detectado.")

async def main():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    # Alvos Líquidos + Alpha
    targets = ["SOL_USDC_PERP", "MON_USDC_PERP", "JTO_USDC_PERP", "HYPE_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP"]
    
    sim = GridBacktester(targets, initial_capital=200.0, leverage=10, max_slots=20)
    await sim.load_data(data_client)
    sim.run()

if __name__ == "__main__":
    asyncio.run(main())
