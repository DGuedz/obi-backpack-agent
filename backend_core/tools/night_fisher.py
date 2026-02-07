
import os
import sys
import asyncio
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle

async def night_fisher_analysis():
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    # Ativos com Fluxo On-Chain Confirmado (Passo anterior)
    targets = [
        {"symbol": "ETH_USDC_PERP", "bias": "LONG"},  # Whales Buying
        {"symbol": "SUI_USDC_PERP", "bias": "LONG"},  # Whales Buying
        {"symbol": "BTC_USDC_PERP", "bias": "LONG"},  # Trend Bullish
        # DOGE já estamos Shortados
    ]
    
    print("\n NIGHT FISHER STRATEGY (Passive Income)")
    print("Buscando pontos de entrada passivos (Limit Maker) em suportes/resistências chave.")
    print("-" * 100)
    print(f"{'SYMBOL':<15} | {'BIAS':<6} | {'CURRENT':<10} | {'ENTRY (LIMIT)':<14} | {'DIST%':<8} | {'REASON':<20}")
    print("-" * 100)
    
    fishing_orders = []
    
    for t in targets:
        symbol = t['symbol']
        bias = t['bias']
        
        try:
            # Pegar Candles de 1H para trend macro da noite
            klines = data_client.get_klines(symbol, "1h", limit=100)
            if not klines: continue
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            df['low'] = df['low'].astype(float)
            df['high'] = df['high'].astype(float)
            
            current_price = df['close'].iloc[-1]
            
            # Estratégia: Mean Reversion to EMA50 (1h) ou Order Block recente
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            entry_price = 0.0
            reason = ""
            
            if bias == "LONG":
                # Compra no "Reteste" (Pullback)
                # Ideal: Entre EMA20 e EMA50
                support_zone = (ema_20 + ema_50) / 2
                
                # Refinamento: Pegar o fundo mais recente (Fractal Low)
                last_low = df['low'].tail(5).min()
                
                # O Entry é o maior valor entre (EMA50) e (Last Low - 0.5%)
                # Queremos pegar o pavio (wick)
                entry_price = min(support_zone, last_low)
                reason = "EMA Pullback Zone"
                
                # Se preço atual já estiver abaixo da EMA, ajusta para suporte mais fundo
                if current_price < ema_20:
                    entry_price = df['low'].tail(24).min() # Mínima do dia
                    reason = "Daily Low Support"

            elif bias == "SHORT":
                resistance_zone = (ema_20 + ema_50) / 2
                last_high = df['high'].tail(5).max()
                entry_price = max(resistance_zone, last_high)
                reason = "Resistance Retest"
            
            # Calcular Distância
            dist_pct = ((entry_price - current_price) / current_price) * 100
            
            # Formatação de Preço
            if "BTC" in symbol: entry_price = round(entry_price, 1)
            elif "ETH" in symbol: entry_price = round(entry_price, 2)
            else: entry_price = round(entry_price, 4)
            
            print(f"{symbol:<15} | {bias:<6} | {current_price:<10.4f} | {entry_price:<14.4f} | {dist_pct:<+7.2f}% | {reason:<20}")
            
            fishing_orders.append({
                "symbol": symbol,
                "side": "Bid" if bias == "LONG" else "Ask",
                "price": entry_price,
                "dist": abs(dist_pct)
            })
            
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
            
    print("-" * 100)
    if fishing_orders:
        print("\n RECOMENDAÇÃO TÁTICA (Executar agora para acordar no lucro):")
        for order in fishing_orders:
            if order['dist'] < 5.0: # Só aceita se estiver a menos de 5% de distância
                print(f"   -> Colocar ORDEM LIMIT {order['side']} em {order['symbol']} @ {order['price']}")

if __name__ == "__main__":
    asyncio.run(night_fisher_analysis())
