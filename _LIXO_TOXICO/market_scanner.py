
import os
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def analyze_market():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print(" Coletando dados da Backpack...")
    tickers = data.get_tickers()
    
    if not tickers:
        print("Erro ao buscar tickers.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(tickers)
    
    # Ensure numeric columns
    numeric_cols = ['lastPrice', 'volume', 'high', 'low', 'open']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(float)

    # 1. Volume Analysis
    top_vol = df.sort_values(by='volume', ascending=False).head(5)
    
    # 2. Volatility (High/Low spread)
    df['volatility'] = (df['high'] - df['low']) / df['low']
    top_volat = df.sort_values(by='volatility', ascending=False).head(5)
    
    # 3. Funding Rates (Need Mark Prices)
    # Note: get_tickers might not have funding. Let's try to get specific perp tickers or mark prices if available.
    # The standard ticker endpoint usually has 'markPrice' or we need 'get_mark_prices'.
    # Let's check columns first.
    
    print("\n RELATÓRIO DE SEGUNDA-FEIRA (BACKPACK ON-CHAIN)")
    print("=================================================")
    
    print("\n Top 5 Volume (Onde está o dinheiro):")
    for _, row in top_vol.iterrows():
        print(f"   - {row['symbol']}: Vol {row['volume']:,.0f} | Preço ${row['lastPrice']}")

    print("\n Top 5 Volatilidade (Onde está o perigo/oportunidade):")
    for _, row in top_volat.iterrows():
        print(f"   - {row['symbol']}: {row['volatility']*100:.2f}% (Range do dia)")
        
    # Tentar buscar Funding Rates via Mark Prices
    try:
        marks = data.get_mark_prices()
        # Assuming marks is a list of dicts with 'symbol' and 'fundingRate'
        # Need to verify structure. Based on previous usage it might be.
        if marks:
            df_marks = pd.DataFrame(marks)
            if 'fundingRate' in df_marks.columns:
                df_marks['fundingRate'] = df_marks['fundingRate'].astype(float)
                avg_funding = df_marks['fundingRate'].mean()
                
                print("\n️ Temperatura do Mercado (Funding Rate):")
                print(f"   - Média Global: {avg_funding*100:.4f}%")
                if avg_funding > 0.01:
                    print("   - Veredito: ALAVANCAGEM BULLISH (Longs pagando Shorts)")
                elif avg_funding < 0:
                    print("   - Veredito: ALAVANCAGEM BEARISH (Shorts pagando Longs)")
                else:
                    print("   - Veredito: NEUTRO (Equilíbrio)")
                    
                top_funding = df_marks.sort_values(by='fundingRate', ascending=False).head(3)
                print("   - Mais Caros para Longar (Hype):", ", ".join([f"{x['symbol']} ({x['fundingRate']*100:.3f}%)" for _, x in top_funding.iterrows()]))
    except Exception as e:
        print(f"\n️ Não foi possível analisar Funding: {e}")

if __name__ == "__main__":
    analyze_market()
