import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def analyze_market_state():
    print(" BOM DIA, MESTRE. ANÁLISE DE MERCADO (COMPARATIVO)", flush=True)
    print("===================================================")
    
    try:
        auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        data = BackpackData(auth)
        
        # 1. Obter Dados Gerais (Tickers)
        print(" Buscando Tickers...", flush=True)
        tickers = data.get_tickers()
        if not tickers:
            print(" Erro ao obter dados de mercado (Lista Vazia).", flush=True)
            return

        print(f" {len(tickers)} Tickers recebidos.", flush=True)
        df = pd.DataFrame(tickers)
        
        # Filtrar apenas PERPs USDC
        df = df[df['symbol'].str.contains('USDC_PERP')]
        
        # Converter colunas
        cols = ['lastPrice', 'priceChangePercent', 'volume', 'quoteVolume', 'high', 'low']
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c])

        # 2. Análise de Sentimento (Funding Rate)
        # Nota: Tickers endpoint as vezes tem funding, ou precisamos de get_mark_prices
        mark_prices = data.get_mark_prices()
        df_mark = pd.DataFrame(mark_prices)
        
        funding_rates = []
        if not df_mark.empty and 'fundingRate' in df_mark.columns:
            df_mark['fundingRate'] = pd.to_numeric(df_mark['fundingRate'])
            funding_rates = df_mark['fundingRate']
            
            avg_funding = funding_rates.mean()
            max_funding = funding_rates.max()
            min_funding = funding_rates.min()
            
            # Interpretação
            sentiment = "NEUTRO"
            if avg_funding > 0.01: sentiment = "EXTREMAMENTE BULLISH (Alavancado)"
            elif avg_funding > 0.001: sentiment = "BULLISH (Saudável)"
            elif avg_funding < -0.001: sentiment = "BEARISH"
            
            print(f"\n SENTIMENTO GLOBAL (Funding Rates):")
            print(f"   Média: {avg_funding*100:.4f}% | {sentiment}")
            print(f"   Max (Longs pagando): {max_funding*100:.4f}%")
            print(f"   Min (Shorts pagando): {min_funding*100:.4f}%")
        
        # 3. Volatilidade (High/Low Spread)
        df['volatility'] = (df['high'] - df['low']) / df['low']
        avg_volat = df['volatility'].mean()
        
        # Comparativo Heurístico (Baseado em dias típicos)
        # Madrugada Típica: ~2-3% Volatilidade média em Alts
        vol_status = "NORMAL"
        if avg_volat > 0.05: vol_status = "ALTA (Agitado)"
        elif avg_volat < 0.02: vol_status = "BAIXA (Consolidação)"
        
        print(f"\n VOLATILIDADE (Risco/Oportunidade):")
        print(f"   Média do Mercado: {avg_volat*100:.2f}% ({vol_status})")
        
        # Top Movers
        top_gainers = df.sort_values(by='priceChangePercent', ascending=False).head(3)
        top_losers = df.sort_values(by='priceChangePercent', ascending=True).head(3)
        
        print(f"\n DESTAQUES (24h):")
        for _, r in top_gainers.iterrows():
            print(f"   🟢 {r['symbol']}: +{r['priceChangePercent']:.2f}% (Vol: {r['volatility']*100:.1f}%)")
            
        print(f"\n SANGRAMENTO (24h):")
        for _, r in top_losers.iterrows():
            print(f"    {r['symbol']}: {r['priceChangePercent']:.2f}%")

        # 4. BTC & SOL Check
        print(f"\n LÍDERES:")
        for sym in ["BTC_USDC_PERP", "SOL_USDC_PERP", "ETH_USDC_PERP"]:
            row = df[df['symbol'] == sym]
            if not row.empty:
                price = row.iloc[0]['lastPrice']
                change = row.iloc[0]['priceChangePercent']
                vol = row.iloc[0]['volatility']
                print(f"   {sym.split('_')[0]}: ${price:,.2f} ({change:+.2f}%) | Vol Dia: {vol*100:.2f}%")
                
    except Exception as e:
        print(f" Erro Crítico: {e}", flush=True)

if __name__ == "__main__":
    analyze_market_state()
