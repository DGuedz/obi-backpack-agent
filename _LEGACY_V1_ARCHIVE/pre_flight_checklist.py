import time
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators
from technical_oracle import MarketProxyOracle

class UltimateChecklist:
    def __init__(self, symbol):
        load_dotenv()
        self.symbol = symbol
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_engine = BackpackData(self.auth)
        self.indicators = BackpackIndicators()
        self.oracle = MarketProxyOracle(symbol, self.auth, self.data_engine)
        
        # Parâmetros de Rigor (Hardcoded Discipline)
        self.MAX_SPREAD_PCT = 0.0015  # 0.15% (Acima disso, o spread come o lucro)
        self.MIN_24H_VOLUME = 500_000 # Adjusted from 10M to 500k to allow mid-caps, but strict enough
        self.RISK_LIMIT_PCT = 0.02    # Max 2% de risco por trade

    def _get_fear_and_greed(self):
        """Camada 1: Sentimento Macro (Via API Pública Alternative.me)"""
        try:
            response = requests.get("https://api.alternative.me/fng/")
            data = response.json()
            value = int(data['data'][0]['value']) # Corrected indexing for FNG API
            return value
        except:
            return 50 # Neutro em caso de falha de rede

    def run_full_scan(self, side, leverage, balance=None):
        """
        O GRANDE JUIZ.
        Retorna: (Bool, Reason)
        True = Trade Aprovado.
        False = Trade Bloqueado (Com o motivo).
        """
        print(f"\n️ INICIANDO CHECKLIST DE 5 CAMADAS PARA {self.symbol} ({side})...")
        
        # -----------------------------------------------------------
        # CAMADA 1: SAÚDE DO ATIVO (Liquidez & Spread) [Source 1547]
        # -----------------------------------------------------------
        ticker = self.data_engine.get_ticker(self.symbol)
        if not ticker:
             return False, " REJEITADO: Falha ao obter Ticker."

        quote_vol = float(ticker.get('quoteVolume', 0))
        
        # Fallback for bestBid/Ask using lastPrice if unavailable
        best_bid = float(ticker.get('bestBid', ticker.get('lastPrice')))
        best_ask = float(ticker.get('bestAsk', ticker.get('lastPrice')))
        
        # 1.1 Volume Check
        if quote_vol < self.MIN_24H_VOLUME:
            return False, f" REJEITADO: Volume Baixo (${quote_vol:,.2f}). Risco de manipulação."
            
        # 1.2 Spread Check
        if best_bid > 0:
            spread = (best_ask - best_bid) / best_bid
            if spread > self.MAX_SPREAD_PCT:
                return False, f" REJEITADO: Spread Caro ({spread*100:.3f}%). Custo de entrada inviável."
        
        print(" CAMADA 1 (Liquidez): Aprovada.")

        # -----------------------------------------------------------
        # CAMADA 2: SENTIMENTO MACRO & FUNDING [Source 1870, 1570]
        # -----------------------------------------------------------
        fng = self._get_fear_and_greed()
        bias, funding_rate = self.oracle.get_funding_bias()
        
        # 2.1 Regra do Funding (Não nadar contra a maré)
        # Se Funding Positivo (>0), a manada está LONG. O Smart Money procura SHORT ou Yield.
        if side == "Buy" and funding_rate > 0.0005: # 0.05% Funding
            return False, f" REJEITADO: Funding Tax muito alto para Long ({funding_rate*100:.4f}%). Você vai pagar para segurar."
        
        # 2.2 Fear & Greed (Evitar Long no Topo / Short no Fundo)
        if side == "Buy" and fng > 80:
            return False, f" REJEITADO: Extreme Greed ({fng}). Risco de Topo."
        if side == "Sell" and fng < 20:
            return False, f" REJEITADO: Extreme Fear ({fng}). Risco de Fundo (Late Short)."

        print(f" CAMADA 2 (Macro): Aprovada. (Funding: {funding_rate:.5f} | F&G: {fng})")

        # -----------------------------------------------------------
        # CAMADA 3: PROXY ON-CHAIN (Order Book Imbalance) [Source 1567]
        # -----------------------------------------------------------
        obi = self.oracle.get_order_book_imbalance()
        
        # OBI varia de -1 (Venda Forte) a +1 (Compra Forte)
        if side == "Buy" and obi < -0.2:
            return False, f" REJEITADO: OBI Bearish ({obi:.2f}). Parede de Venda detectada."
        if side == "Sell" and obi > 0.2:
            return False, f" REJEITADO: OBI Bullish ({obi:.2f}). Parede de Compra detectada."

        print(" CAMADA 3 (On-Chain Proxy): Aprovada.")

        # -----------------------------------------------------------
        # CAMADA 4: TÉCNICA (Indicadores & Confluência) [Source 1543-1546]
        # -----------------------------------------------------------
        klines = self.data_engine.get_klines(self.symbol, interval='1h', limit=200)
        df = pd.DataFrame(klines)
        
        if 'close' not in df.columns:
             # Try fallback to standard numeric columns if dict fails or keys differ
             pass
        
        # Type casting
        try:
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)
        except:
            return False, " REJEITADO: Dados de Klines inválidos."

        # EMA 200 (Tendência Macro) - Usando BackpackIndicators ou pandas rolling
        # BackpackIndicators has ema_cross but not raw EMA? Let's use simple rolling EWMA
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
        last_close = df['close'].iloc[-1]
        
        # Handle cases with insufficient data for EMA200
        if pd.isna(df['ema200'].iloc[-1]):
             df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
             ema_val = df['ema50'].iloc[-1]
             if pd.isna(ema_val):
                 return False, " REJEITADO: Histórico insuficiente para indicadores."
        else:
             ema_val = df['ema200'].iloc[-1]
        
        # RSI (Momentum) - Using BackpackIndicators
        df['rsi'] = self.indicators.calculate_rsi(df, window=14)
        rsi_val = df['rsi'].iloc[-1]

        # Regras de Ouro da Confluência
        if side == "Buy":
            if last_close < ema_val:
                return False, f" REJEITADO: Preço abaixo da EMA ({last_close} < {ema_val:.2f}). Tendência de Baixa."
            if rsi_val > 70:
                return False, f" REJEITADO: RSI Sobrecomprado ({rsi_val:.2f}). Espere o pullback."
                
        elif side == "Sell":
            if last_close > ema_val:
                return False, f" REJEITADO: Preço acima da EMA ({last_close} > {ema_val:.2f}). Tendência de Alta."
            if rsi_val < 30:
                return False, f" REJEITADO: RSI Sobrevendido ({rsi_val:.2f}). Risco de repique."

        print(" CAMADA 4 (Técnica): Aprovada.")

        # -----------------------------------------------------------
        # CAMADA 5: PROTOCOLO DE RISCO (Stop Loss & Size) [Source 48, 691]
        # -----------------------------------------------------------
        # Cálculo obrigatório de Stop Loss antes da entrada
        # ATR using BackpackIndicators
        atr_series = self.indicators.calculate_atr(df, window=14)
        atr = atr_series.iloc[-1]
        
        if side == "Buy":
            stop_loss_price = last_close - (atr * 1.5)
            potential_loss = (last_close - stop_loss_price) / last_close
        else:
            stop_loss_price = last_close + (atr * 1.5)
            potential_loss = (stop_loss_price - last_close) / last_close
            
        # Risco x Alavancagem
        total_risk = potential_loss * leverage
        
        # Se o risco do trade (distancia do stop * alavancagem) for maior que 100%, é liquidação garantida.
        if total_risk >= 0.8: # 80% margin usage risk
             return False, f" REJEITADO: Stop Loss muito distante para essa alavancagem. Risco de Liq: {total_risk*100:.2f}%"

        print(f" CAMADA 5 (Risco): Aprovada. SL Calculado: {stop_loss_price:.4f} (Risk: {total_risk*100:.2f}%)")

        # -----------------------------------------------------------
        # VEREDITO FINAL
        # -----------------------------------------------------------
        return True, {
            "sl_price": stop_loss_price,
            "entry_price": last_close,
            "atr": atr,
            "confidence_score": "HIGH"
        }
