from pre_flight_checklist import UltimateChecklist
import pandas as pd
import numpy as np

class ScalpChecklist(UltimateChecklist):
    def __init__(self, symbol):
        super().__init__(symbol)
        # Scalp parameters: tighter spread, faster reaction
        self.MAX_SPREAD_PCT = 0.002  # Allow slightly more spread for volatility
        self.MIN_24H_VOLUME = 500_000 # $500k Min for liquidity

    def run_fast_scan(self, side, leverage):
        """
        Versão Turbo do Protocolo de 5 Camadas para Scalp.
        Usa candles de 5m e 15m em vez de 1h.
        """
        print(f"\n INICIANDO CHECKLIST ULTRA-SCALP PARA {self.symbol} ({side})...")
        
        # -----------------------------------------------------------
        # CAMADA 1: SAÚDE DO ATIVO (Liquidez & Spread)
        # -----------------------------------------------------------
        ticker = self.data_engine.get_ticker(self.symbol)
        if not ticker: return False, "Falha no Ticker"
        
        # Spread Check
        best_bid = float(ticker.get('bestBid', ticker.get('lastPrice')))
        best_ask = float(ticker.get('bestAsk', ticker.get('lastPrice')))
        if best_bid > 0:
            spread = (best_ask - best_bid) / best_bid
            if spread > self.MAX_SPREAD_PCT:
                return False, f" REJEITADO: Spread ({spread*100:.3f}%) muito alto para Scalp."

        print(" CAMADA 1 (Liquidez): OK")

        # -----------------------------------------------------------
        # CAMADA 2: MACRO (Ignora F&G, foca no Funding)
        # -----------------------------------------------------------
        bias, funding_rate = self.oracle.get_funding_bias()
        if side == "Buy" and funding_rate > 0.001: # 0.1% Funding is too expensive
            return False, f" REJEITADO: Funding ({funding_rate*100:.4f}%) alto."
            
        print(" CAMADA 2 (Macro): OK")

        # -----------------------------------------------------------
        # CAMADA 3: PROXY ON-CHAIN (OBI - Critical)
        # -----------------------------------------------------------
        obi = self.oracle.get_order_book_imbalance()
        # Scalp requires momentum flow
        if side == "Buy" and obi < -0.1: # Allow slight negative but not wall
             return False, f" REJEITADO: OBI Bearish ({obi:.2f})."
        if side == "Sell" and obi > 0.1:
             return False, f" REJEITADO: OBI Bullish ({obi:.2f})."
             
        print(" CAMADA 3 (Flow): OK")

        # -----------------------------------------------------------
        # CAMADA 4: TÉCNICA (5m Timeframe)
        # -----------------------------------------------------------
        klines = self.data_engine.get_klines(self.symbol, interval='5m', limit=100)
        df = pd.DataFrame(klines)
        if df.empty: return False, "Sem dados 5m"
        
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        # EMA 50 (Trend Fast)
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        last_close = df['close'].iloc[-1]
        ema_val = df['ema50'].iloc[-1]
        
        # RSI (Momentum)
        df['rsi'] = self.indicators.calculate_rsi(df, window=14)
        rsi_val = df['rsi'].iloc[-1]
        
        if side == "Buy":
            # Scalp Long: Price > EMA50 OR RSI Oversold Bounce
            if last_close < ema_val and rsi_val > 35: 
                return False, f" REJEITADO: Abaixo da EMA 50 (5m) e sem RSI extremo."
        elif side == "Sell":
            if last_close > ema_val and rsi_val < 65:
                return False, f" REJEITADO: Acima da EMA 50 (5m) e sem RSI extremo."
                
        print(" CAMADA 4 (Técnica 5m): OK")

        # -----------------------------------------------------------
        # CAMADA 5: RISCO (Fixed 1.5% SL)
        # -----------------------------------------------------------
        atr_series = self.indicators.calculate_atr(df, window=14)
        atr = atr_series.iloc[-1]
        
        # User defined fixed Stop Loss of 1.5% move
        SL_PERCENT = 0.015 # 1.5%
        
        if side == "Buy":
            sl_price = last_close * (1 - SL_PERCENT)
        else:
            sl_price = last_close * (1 + SL_PERCENT)
            
        print(f" CAMADA 5 (Risco): OK. SL (1.5%): {sl_price}")
        
        return True, {
            "sl_price": sl_price,
            "entry_price": last_close,
            "atr": atr,
            "confidence_score": "SCALP"
        }
