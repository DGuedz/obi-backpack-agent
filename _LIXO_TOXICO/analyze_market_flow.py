import os
import sys
import pandas as pd
import requests
import datetime
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

# --- Configuração ---
HOLDINGS = ["HYPE_USDC_PERP", "ETH_USDC_PERP", "PENGU_USDC_PERP", "SOL_USDC_PERP", "kBONK_USDC_PERP"]

class MarketFlowAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.private_key = os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(self.api_key, self.private_key)
        self.data = BackpackData(self.auth)
        self.base_url = "https://api.backpack.exchange"

    def get_open_interest(self, symbol):
        try:
            url = f"{self.base_url}/api/v1/openInterest"
            res = requests.get(url, params={'symbol': symbol})
            if res.status_code == 200:
                data = res.json()
                # Pode retornar lista ou dict
                if isinstance(data, list) and len(data) > 0:
                    return float(data[0].get('openInterest', 0))
                return 0.0
        except:
            return 0.0
        return 0.0

    def analyze_trend(self, symbol):
        # Pegar velas de 1h para tendência de curto/médio prazo
        klines = self.data.get_klines(symbol, interval="1h", limit=50)
        if not klines:
            return "UNKNOWN", 0, 0
            
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        
        # EMA 20 (Tendência Curta)
        ema20 = df['close'].ewm(span=20).mean().iloc[-1]
        price = df['close'].iloc[-1]
        
        # RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = rsi.iloc[-1]
        
        trend = "BEARISH" if price < ema20 else "BULLISH"
        
        return trend, price, rsi_val

    def run_analysis(self):
        print(" ANALISANDO FLUXO DE MERCADO E TENDÊNCIA...")
        print("-" * 60)
        
        # 1. Onde está o dinheiro? (Volume Analysis)
        tickers = self.data.get_tickers()
        
        # Converter para lista se necessário e filtrar PERPs
        perp_tickers = [t for t in tickers if 'PERP' in t['symbol']]
        
        # Ordenar por Quote Volume (Dinheiro negociado)
        perp_tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        
        print(f" TOP 5 VOLUME (Onde o dinheiro está agora):")
        for i, t in enumerate(perp_tickers[:5]):
            vol_millions = float(t['quoteVolume']) / 1_000_000
            change_24h = float(t.get('priceChangePercent', 0))
            print(f"   {i+1}. {t['symbol']:<15} | Vol: ${vol_millions:.1f}M | 24h: {change_24h:+.2f}%")
            
        print("-" * 60)
        
        # 2. Análise das Nossas Posições
        print("️ DIAGNÓSTICO DAS POSIÇÕES (Estamos contra o mercado?):")
        
        contra_trend_count = 0
        
        for symbol in HOLDINGS:
            # Buscar dados específicos
            ticker = next((t for t in perp_tickers if t['symbol'] == symbol), None)
            if not ticker: continue
            
            trend, price, rsi = self.analyze_trend(symbol)
            funding = float(ticker.get('fundingRate', 0)) * 100 # Em %
            oi = self.get_open_interest(symbol)
            
            # Análise de "Contra-Tendência"
            # Se estamos LONG, mas Trend é BEARISH -> PERIGO
            # Se Funding é Negativo -> Bearish Sentiment (Shorts pagando Longs é raro, geralmente Longs pagam Shorts em Bull)
            # Funding Positivo Alto -> Bullish Sentiment excessivo?
            
            status = " A FAVOR"
            if trend == "BEARISH":
                status = " CONTRA A TENDÊNCIA (EMA20 1h)"
                contra_trend_count += 1
            
            print(f"\n    {symbol}")
            print(f"      Preço: {price} | RSI(1h): {rsi:.1f}")
            print(f"      Tendência 1h: {trend} ({status})")
            print(f"      Funding: {funding:.4f}% | OI: {oi:.0f}")
            
            if rsi < 30:
                print("       OPORTUNIDADE: RSI Oversold (Repique provável)")
            elif rsi > 70:
                print("      ️ ALERTA: RSI Overbought (Correção provável)")

        print("-" * 60)
        print(" CONCLUSÃO:")
        if contra_trend_count >= 3:
            print(" ESTAMOS NADANDO CONTRA A MARÉ!")
            print("A maioria das suas posições Long está abaixo da EMA20 (1h).")
            print("O mercado está em correção de curto prazo.")
            print(">> AÇÃO RECOMENDADA: Apertar Stop Loss ou aguardar repique de RSI para sair no 0x0.")
        else:
            print(" Estamos alinhados ou mistos. Mantenha o monitoramento.")

if __name__ == "__main__":
    analyzer = MarketFlowAnalyzer()
    analyzer.run_analysis()
