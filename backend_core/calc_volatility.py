import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
data = BackpackData(auth)

symbol = "SOL_USDC_PERP"
interval = "15m" # Usando 15m para capturar a volatilidade de curto prazo relevante para scalp

print(f"---  ANÁLISE DE VOLATILIDADE (Bollinger) - {symbol} [{interval}] ---")

# 1. Obter Klines
klines = data.get_klines(symbol, interval, limit=100)
if not klines:
    print("Erro ao obter Klines.")
    sys.exit(1)

df = pd.DataFrame(klines)
df['close'] = df['close'].astype(float)
df['high'] = df['high'].astype(float)
df['low'] = df['low'].astype(float)

# 2. Calcular Bollinger Bands (20, 2)
period = 20
std_dev_mult = 2

df['sma'] = df['close'].rolling(window=period).mean()
df['std'] = df['close'].rolling(window=period).std()
df['upper'] = df['sma'] + (df['std'] * std_dev_mult)
df['lower'] = df['sma'] - (df['std'] * std_dev_mult)

# 3. Calcular Volatilidade (Band Width %)
# Band Width = (Upper - Lower) / SMA
df['band_width_pct'] = (df['upper'] - df['lower']) / df['sma']

# 4. Calcular ATR (Average True Range) para comparação
df['tr'] = np.maximum(
    df['high'] - df['low'],
    np.maximum(
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    )
)
df['atr'] = df['tr'].rolling(window=14).mean()
df['atr_pct'] = df['atr'] / df['close']

# Pegar os dados mais recentes
latest = df.iloc[-1]
avg_volatility = df['band_width_pct'].tail(10).mean() # Média das últimas 10 velas

print(f"\nPreço Atual: {latest['close']:.2f}")
print(f"Bollinger Upper: {latest['upper']:.2f}")
print(f"Bollinger Lower: {latest['lower']:.2f}")
print(f"\n--- MÉTRICAS DE RISCO ---")
print(f" Largura da Banda (Volatilidade Atual): {latest['band_width_pct']*100:.3f}%")
print(f" Média Volatilidade (Last 10): {avg_volatility*100:.3f}%")
print(f"ATR (14) - Movimento Médio/Vela: {latest['atr']:.4f} ({latest['atr_pct']*100:.3f}%)")

# Recomendação de Stop
recommended_sl_tight = latest['atr_pct'] * 1.5 # 1.5x ATR
recommended_sl_safe = latest['band_width_pct'] / 4 # 1/4 da Banda (Arbitrário conservador)

print(f"\n--- ️ RECOMENDAÇÃO DE STOP LOSS ---")
print(f"TIGHT (Scalp Rápido - 1.5x ATR): {recommended_sl_tight*100:.3f}%")
print(f"SAFE (Dentro da Banda - 0.25x Width): {recommended_sl_safe*100:.3f}%")

if recommended_sl_tight > 0.001:
    print("\n️ O SL fixo de 0.1% é suicídio matemático com a volatilidade atual.")
    print(f"O mercado oscila {latest['atr_pct']*100:.3f}% por candle normalmente.")
else:
    print("\n O SL de 0.1% parece seguro (Volatilidade baixíssima).")
