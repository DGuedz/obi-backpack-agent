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

async def analyze_correlation():
    print(f"\n️ ANÁLISE DE HEDGE (CORRELAÇÃO & BETA)")
    print("-" * 60)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    # Ativos
    target = "SKR_USDC_PERP"
    hedge_assets = ["SOL_USDC_PERP", "BTC_USDC_PERP"]
    
    # Buscar dados (Limit 500 para ter relevância estatística)
    print(f" Baixando dados de {target} e Hedges...")
    
    klines_target = data_client.get_klines(target, "15m", limit=500)
    if not klines_target: return
    
    df_target = pd.DataFrame(klines_target)
    df_target['close'] = df_target['close'].astype(float)
    returns_target = df_target['close'].pct_change().dropna()
    
    print(f"{'HEDGE ASSET':<15} | {'CORRELAÇÃO':<10} | {'BETA':<10} | {'VOLATILIDADE':<12}")
    print("-" * 60)
    
    best_hedge = None
    best_corr = 0
    
    for asset in hedge_assets:
        klines_hedge = data_client.get_klines(asset, "15m", limit=500)
        if not klines_hedge: continue
        
        df_hedge = pd.DataFrame(klines_hedge)
        df_hedge['close'] = df_hedge['close'].astype(float)
        returns_hedge = df_hedge['close'].pct_change().dropna()
        
        # Alinhar tamanhos (Interseção de índices se necessário, mas aqui assume sequencial igual)
        min_len = min(len(returns_target), len(returns_hedge))
        r_target = returns_target.iloc[-min_len:]
        r_hedge = returns_hedge.iloc[-min_len:]
        
        # Correlação
        correlation = r_target.corr(r_hedge)
        
        # Beta (Covariância / Variância do Mercado)
        covariance = np.cov(r_target, r_hedge)[0][1]
        variance = np.var(r_hedge)
        beta = covariance / variance
        
        # Volatilidade Relativa
        vol_target = r_target.std()
        vol_hedge = r_hedge.std()
        vol_ratio = vol_target / vol_hedge
        
        print(f"{asset:<15} | {correlation:<10.4f} | {beta:<10.4f} | {vol_ratio:<12.2f}x")
        
        if correlation > best_corr:
            best_corr = correlation
            best_hedge = asset
            best_beta = beta

    print("-" * 60)
    print(" CONCLUSÃO TÁTICA:")
    if best_hedge:
        print(f" Melhor Hedge: {best_hedge}")
        print(f"   Correlação: {best_corr:.2f} (Quanto maior, melhor o hedge)")
        print(f"   Beta: {best_beta:.2f} (Para cada 1% que {best_hedge} move, {target} move {best_beta:.2f}%)")
        print(f"\n ESTRATÉGIA DE PROTEÇÃO (DELTA NEUTRAL):")
        print(f"   Para cada $1000 em {target} (Long),")
        print(f"   Abra SHORT de ${1000 * best_beta:.2f} em {best_hedge}.")
        print("   Isso isola o 'Alpha' (movimento próprio do SKR) e remove o risco de mercado.")

if __name__ == "__main__":
    asyncio.run(analyze_correlation())
