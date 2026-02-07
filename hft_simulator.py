
import os
import sys
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Import Core Modules
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators

# --- HFT CONFIG ---
LEVERAGE = 10
INITIAL_CAPITAL = 200 # Margin
# Ajuste Fino para Scalp (Baseado em 10x)
# SL 1% da Margem = 0.1% Price Move
# TP 5% da Margem = 0.5% Price Move
SL_PCT = 0.001 
TP_PCT = 0.005 
COMPOUNDING = True # "Mao maior"

class HFTSimulator:
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.indicators = BackpackIndicators()
        
    def get_top_vol_assets(self, limit=20):
        print("    Scanning Top 20 High Volume Assets...")
        tickers = self.data.get_tickers()
        perps = [t for t in tickers if t['symbol'].endswith('_PERP')]
        perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        return [p['symbol'] for p in perps[:limit]]

    def run_hft_backtest(self, symbol):
        # Fetch 1m Candles (Max precision available via API usually)
        # We need enough data for 20 trades.
        klines = self.data.get_klines(symbol, "1m", limit=1000) 
        if not klines: return None
        
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['timestamp'] = pd.to_datetime(df['start'])
        
        # Indicator: EMA 50 on 1m (Trend)
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Indicator: RSI 14 on 1m
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        capital = INITIAL_CAPITAL
        trades = []
        
        # SIMULAÇÃO: 3 CENÁRIOS PARALELOS
        # 1. Trend Pullback (Tendência + RSI Extremo)
        # 2. Breakout (Rompimento de Volume)
        # 3. Mean Reversion (Bollinger/RSI puro)
        
        # Vamos focar no CENÁRIO 1 (Trend Pullback) que é o nosso Core.
        # Se vencer 2 de 3 tentativas recentes, valida o ativo.
        
        # Para simular "2 de 3", vamos olhar janelas deslizantes de 3 sinais.
        
        signals = []
        
        # Start loop after indicators stabilize
        for i in range(50, len(df)):
            row = df.iloc[i]
            price = row['close']
            prev_row = df.iloc[i-1]
            
            # SIGNAL GENERATION (Trend Pullback)
            signal = None
            
            # LONG: Price > EMA50 AND RSI < 40
            if price > row['ema50'] and row['rsi'] < 40:
                signal = "LONG"
            # SHORT: Price < EMA50 AND RSI > 60
            elif price < row['ema50'] and row['rsi'] > 60:
                signal = "SHORT"
                
            if signal:
                # EXECUTE TRADE SIMULATION (Check next candle or same candle rest)
                # Assumindo entrada no fechamento deste candle (próximo open)
                # Check outcome in next candles (Hold max 5 candles)
                
                entry = price
                sl = entry * (1 - SL_PCT) if signal == "LONG" else entry * (1 + SL_PCT)
                tp = entry * (1 + TP_PCT) if signal == "LONG" else entry * (1 - TP_PCT)
                
                outcome = "TIMEOUT"
                pnl_amount = 0
                
                # Look ahead 5 candles
                for j in range(1, 6):
                    if i + j >= len(df): break
                    future = df.iloc[i+j]
                    
                    if signal == "LONG":
                        if future['low'] <= sl:
                            outcome = "LOSS"
                            pnl_amount = -0.01 * capital # 1% Margin Loss Fixed
                            break
                        elif future['high'] >= tp:
                            outcome = "WIN"
                            pnl_amount = 0.05 * capital # 5% Margin Gain Fixed
                            break
                    else: # SHORT
                        if future['high'] >= sl:
                            outcome = "LOSS"
                            pnl_amount = -0.01 * capital
                            break
                        elif future['low'] <= tp:
                            outcome = "WIN"
                            pnl_amount = 0.05 * capital
                            break
                
                signals.append(outcome)
                if outcome != "TIMEOUT":
                    capital += pnl_amount
        
        # ANALISAR "2 DE 3"
        # Verificar nas últimas 3 simulações se houve 2 vitórias.
        recent_signals = [s for s in signals if s != "TIMEOUT"][-3:]
        wins = recent_signals.count("WIN")
        
        approved = False
        if len(recent_signals) >= 3 and wins >= 2:
            approved = True
            
        return {
            'symbol': symbol,
            'recent_signals': recent_signals,
            'approved': approved,
            'final_capital': capital,
            'trade_count': len(signals)
        }

    def run(self):
        print("\n HFT SIMULATOR: 20 OPERATIONS CHALLENGE ")
        print(f"   Setup: 10x Leverage | SL 1% | TP 5% | Compounding: {COMPOUNDING}")
        print(f"   Data: 1m Candles (Proxy for 1s Execution)")
        print("="*60)
        
        assets = self.get_top_vol_assets()
        best_performer = None
        best_pnl = -999999
        
        print(f"{'SYMBOL':<15} | {'TRADES':<6} | {'WIN RATE':<8} | {'FINAL CAP ($)'} | {'RESULT'}")
        print("-" * 65)
        
        for symbol in assets:
            res = self.run_hft_backtest(symbol)
            if not res or res['trade_count'] == 0: continue
            
            # wins = len([t for t in res['trades'] if t['outcome'] == "WIN"]) # DEPRECATED
            # New Logic: Just check signals
            wins = res['recent_signals'].count("WIN")
            win_rate = (wins / len(res['recent_signals'])) * 100 if len(res['recent_signals']) > 0 else 0
            
            final_cap = res['final_capital']
            pnl_pct = ((final_cap - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
            
            status = " APPROVED" if res['approved'] else " REJECTED"
            
            print(f"{symbol:<15} | {res['trade_count']:<6} | {win_rate:<6.1f}%  | ${final_cap:<11.2f} | {status}")
            
            if pnl_pct > best_pnl and res['approved']:
                best_pnl = pnl_pct
                best_performer = res
                
        print("="*65)
        if best_performer:
            print(f"\n CHAMPION ASSET: {best_performer['symbol']}")
            print(f"   Status: APPROVED (2/3 Recent Wins)")
            print(f"   Recent Signals: {best_performer['recent_signals']}")
        else:
            print(" No profitable assets found with this strict setup.")

if __name__ == "__main__":
    sim = HFTSimulator()
    sim.run()
