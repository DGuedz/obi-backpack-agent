import asyncio
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

async def analyze_btc_sentiment():
    print(f"\n BTC SENTIMENT MONITOR (Reversal Hunter)")
    print(f"   Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    symbol = "BTC_USDC_PERP"
    
    # 1. Dados de Candles (1h e 4h para Trend/Reversal)
    klines_1h = data_client.get_klines(symbol, "1h", limit=100)
    klines_4h = data_client.get_klines(symbol, "4h", limit=50)
    
    if not klines_1h or not klines_4h:
        print(" Erro ao obter dados de klines.")
        return

    df_1h = pd.DataFrame(klines_1h)
    df_1h['close'] = df_1h['close'].astype(float)
    
    df_4h = pd.DataFrame(klines_4h)
    df_4h['close'] = df_4h['close'].astype(float)
    
    current_price = df_1h.iloc[-1]['close']
    
    # 2. RSI Check (1h e 4h)
    def calc_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    rsi_1h = calc_rsi(df_1h['close']).iloc[-1]
    rsi_4h = calc_rsi(df_4h['close']).iloc[-1]
    
    # 3. Order Book Imbalance (OBI)
    depth = data_client.get_orderbook_depth(symbol)
    obi = oracle.calculate_obi(depth)
    
    # 4. Funding Rate (Sentiment Proxy)
    # Se Funding muito positivo -> Muita gente em Long (Risco de Long Squeeze)
    # Se Funding negativo -> Muita gente em Short (Risco de Short Squeeze)
    try:
        ticker = data_client.get_ticker(symbol) # Ticker usually has funding info or mark price
        # Backpack API ticker might not have funding directly, check exchange info or separate endpoint if available.
        # Fallback to simple ticker print if funding not found easily in this wrapper
        # Assuming ticker might have it or we infer from premium index if possible.
        # For now, let's use what we have in ticker.
        pass
    except:
        pass

    print(f" Preço BTC: ${current_price:,.2f}")
    print(f" RSI 1h: {rsi_1h:.2f} | RSI 4h: {rsi_4h:.2f}")
    print(f"️ OBI (Fluxo): {obi:.2f} ({'🟢 Compra' if obi > 0 else ' Venda'})")
    
    print("-" * 60)
    print(" ANÁLISE DE REVERSÃO:")
    
    risk_score = 0
    
    # RSI Analysis
    if rsi_1h > 75 or rsi_4h > 75:
        print("   ️ RSI ESTICADO (Overbought). Risco de correção imediata.")
        risk_score += 2
    elif rsi_1h < 25 or rsi_4h < 25:
        print("    RSI NO FUNDO (Oversold). Possível fundo local.")
        risk_score -= 2
    else:
        print("    RSI Saudável (Zona Neutra).")
        
    # OBI Analysis
    if obi < -0.3:
        print("    Pressão Vendedora forte no Book (Paredes de Venda).")
        if rsi_1h > 50:
             print("   ️ Divergência: Preço subindo mas Book vendendo (Absorção). Cuidado.")
             risk_score += 1
    elif obi > 0.3:
        print("   🟢 Pressão Compradora forte no Book.")
        
    # Price Action
    ema_20_1h = df_1h['close'].ewm(span=20).mean().iloc[-1]
    dist_to_ema = (current_price - ema_20_1h) / ema_20_1h
    
    if dist_to_ema > 0.03: # 3% longe da média
        print(f"   ️ Preço muito longe da média 1h (+{dist_to_ema*100:.2f}%). Elástico esticado.")
        risk_score += 1
    
    print("-" * 60)
    if risk_score >= 2:
        print(" VEREDITO: RISCO ALTO DE PULLBACK/REVERSÃO.")
        print("   Recomendação: Apertar Stop Loss (Trailing) e evitar novas entradas Long agressivas.")
    elif risk_score <= -2:
        print(" VEREDITO: OPORTUNIDADE DE COMPRA (FUNDO).")
        print("   Recomendação: Procurar gatilhos de Long (Reversal Sniper).")
    else:
        print(" VEREDITO: TENDÊNCIA SUSTENTÁVEL.")
        print("   Recomendação: Seguir operando a favor da tendência.")

if __name__ == "__main__":
    asyncio.run(analyze_btc_sentiment())
