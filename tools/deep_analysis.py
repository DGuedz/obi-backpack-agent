import os
import sys
import asyncio
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

async def deep_analysis():
    load_dotenv()
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    targets = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "HYPE_USDC_PERP"]
    
    print("\n DEEP TECHNICAL ANALYSIS (Chart Patterns & Confluence)")
    print("Analisando Padrões Gráficos, RSI, Bollinger Bands e Sentimento...")
    print("-" * 110)
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'TREND':<8} | {'RSI':<5} | {'BB POSITION':<15} | {'PREDICTION':<15} | {'ENTRY SUGGESTION'}")
    print("-" * 110)
    
    pulse = oracle.get_market_pulse()
    
    for symbol in targets:
        try:
            klines = data_client.get_klines(symbol, "15m", limit=60)
            if not klines: continue
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['open'] = df['open'].astype(float)
            
            current_price = df.iloc[-1]['close']
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            # Indicadores
            rsi = oracle.get_rsi(df)
            upper_bb, mid_bb, lower_bb = oracle.get_bollinger_bands(df)
            
            # Análise de Tendência
            trend = "BULL" if current_price > ema_50 else "BEAR"
            
            # Análise de Bollinger
            bb_status = "NEUTRAL"
            if current_price >= upper_bb: bb_status = "OVERBOUGHT (Upper)"
            elif current_price <= lower_bb: bb_status = "OVERSOLD (Lower)"
            elif current_price > mid_bb: bb_status = "ABOVE MID"
            else: bb_status = "BELOW MID"
            
            # Padrões de Candle (Simples)
            last_candle = df.iloc[-1]
            body = abs(last_candle['close'] - last_candle['open'])
            wick_upper = last_candle['high'] - max(last_candle['close'], last_candle['open'])
            wick_lower = min(last_candle['close'], last_candle['open']) - last_candle['low']
            
            pattern = ""
            if wick_lower > 2 * body and wick_upper < body:
                pattern = "HAMMER (Reversal?)"
            elif wick_upper > 2 * body and wick_lower < body:
                pattern = "SHOOTING STAR (Drop?)"
                
            # Previsão & Sugestão
            prediction = "SIDEWAYS"
            entry_suggestion = "WAIT"
            
            if trend == "BULL":
                if rsi < 40: prediction = "PULLBACK BUY"
                elif rsi > 70: prediction = "OVEREXTENDED"
                else: prediction = "CONTINUATION"
                
                # Sugestão de Entrada (Long)
                # Tentar pegar no toque da EMA50 ou Lower BB
                target_buy = max(ema_50, lower_bb)
                if current_price > target_buy:
                    entry_suggestion = f"LIMIT BUY @ {target_buy:.4f}"
                else:
                    entry_suggestion = "MARKET BUY (Confirm OBI)"
                    
            else: # BEAR
                if rsi > 60: prediction = "RELIEF SELL"
                elif rsi < 30: prediction = "OVERSOLD BOUNCE"
                else: prediction = "DUMP CONTINUATION"
                
                # Sugestão de Entrada (Short)
                # Tentar pegar no repique da EMA50 ou Upper BB
                target_sell = min(ema_50, upper_bb)
                if current_price < target_sell:
                    entry_suggestion = f"LIMIT SELL @ {target_sell:.4f}"
                else:
                    entry_suggestion = "MARKET SELL (Confirm OBI)"
            
            if pulse == "BEARISH" and trend == "BULL":
                prediction = "FAKE PUMP (Risk)"
                entry_suggestion = "NO TRADE (Systemic Risk)"
                
            print(f"{symbol:<15} | {current_price:<10.4f} | {trend:<8} | {rsi:<5.1f} | {bb_status:<15} | {prediction:<15} | {entry_suggestion}")
            if pattern:
                print(f"   ↳ ️ Pattern Detected: {pattern}")
                
        except Exception as e:
            print(f"{symbol:<15} | ERROR: {e}")
            
    print("-" * 110)
    print(f"️ SENTIMENTO DO MERCADO (BTC Pulse): {pulse}")

if __name__ == "__main__":
    asyncio.run(deep_analysis())
