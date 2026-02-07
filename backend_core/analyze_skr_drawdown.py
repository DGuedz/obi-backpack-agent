import asyncio
import pandas as pd
import numpy as np
import sys
import os
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

SYMBOL = "SKR_USDC_PERP"

async def analyze_skr():
    print(f"\n ANÁLISE PROFUNDA DE DRAWDOWN: {SYMBOL}")
    print("-" * 60)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    # 1. Dados Técnicos (1h para Trend, 15m para Momento)
    klines_1h = data_client.get_klines(SYMBOL, "1h", limit=100)
    if not klines_1h:
        print(" Erro ao obter dados.")
        return

    df = pd.DataFrame(klines_1h)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    current_price = df.iloc[-1]['close']
    max_price = df['high'].max()
    min_price = df['low'].min()
    
    drawdown_pct = ((current_price - max_price) / max_price) * 100
    
    # RSI Manual
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    rsi = df.iloc[-1]['rsi']
    
    print(f" Preço Atual: ${current_price:.5f}")
    print(f"️ Topo Recente (100h): ${max_price:.5f}")
    print(f" Drawdown Atual: {drawdown_pct:.2f}%")
    print(f" RSI (1h): {rsi:.2f}")
    
    # 2. Análise de Suporte (Order Book)
    depth = data_client.get_orderbook_depth(SYMBOL)
    if depth:
        bids = depth.get('bids', [])
        # Bids Ascending -> Last is Best Bid
        # Vamos varrer do melhor para o pior (baixo) procurando acumulado
        
        # Inverter para ter do maior preço para o menor
        bids_desc = sorted(bids, key=lambda x: float(x[0]), reverse=True)
        
        print("\n MAPA DE SUPORTES (ORDER BOOK):")
        cumulative_vol = 0.0
        found_support = False
        
        # Procurar onde tem $50k acumulado
        target_absorb = 50000 
        
        for price_str, qty_str in bids_desc:
            price = float(price_str)
            qty = float(qty_str)
            val = price * qty
            cumulative_vol += val
            
            dist_pct = ((price - current_price) / current_price) * 100
            
            # Printar a cada $10k acumulado
            if cumulative_vol >= target_absorb:
                print(f"   ️ Suporte Forte Detectado: ${price:.5f} ({dist_pct:.2f}%) | Vol Acumulado: ${cumulative_vol:,.0f}")
                target_absorb += 50000 # Próximo nível
                found_support = True
                if cumulative_vol > 200000: break # Limite de scan
        
        if not found_support:
            print("   ️ Nenhum suporte significativo próximo (Queda Livre?)")

    # 3. Veredito
    print("-" * 60)
    print(" DIAGNÓSTICO:")
    if rsi < 30:
        print("    OVERSOLD (Sobrevendido). Chance de repique alta.")
    elif rsi > 70:
        print("   ️ OVERBOUGHT. Cuidado com Longs.")
    else:
        print("   ️ NEUTRO. Segue o fluxo.")
        
    if drawdown_pct < -30:
        print("    CRASH SEVERO. Procure por exaustão de venda.")
        
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(analyze_skr())
