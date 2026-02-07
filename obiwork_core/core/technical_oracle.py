import pandas as pd
# import pandas_ta as ta # Removendo dependência de pandas_ta temporariamente
import logging

class TechnicalOracle:
    """
     TECHNICAL ORACLE
    Responsável por calcular indicadores técnicos, fluxo de ordens (OBI) e métricas de risco (ATR).
    Segue a História 1 das Especificações.
    """
    def __init__(self, data_client):
        self.data = data_client
        self.logger = logging.getLogger("TechnicalOracle")

    def get_obi(self, symbol):
        """Wrapper for get_obi to maintain compatibility with VolumeFarmer."""
        depth = self.data.get_orderbook_depth(symbol)
        return self.calculate_obi(depth)

    def calculate_obi(self, depth, detect_spoofing=True):
        """
        Calcula o Order Book Imbalance (OBI).
        OBI = (BidVol - AskVol) / (BidVol + AskVol)
        Range: -1 (Venda Forte) a +1 (Compra Forte).
        
        Args:
            depth (dict): Dados do livro de ordens.
            detect_spoofing (bool): Se True, penaliza ordens desproporcionalmente grandes (paredes falsas).
        """
        try:
            if not depth or 'bids' not in depth or 'asks' not in depth:
                return 0.0

            bids = depth.get('bids', [])
            asks = depth.get('asks', [])

            if not bids or not asks:
                return 0.0

            # Backpack Bids are Ascending (Low -> High), Asks are Ascending (Low -> High)
            # Para pegar os melhores bids (maiores preços), precisamos dos últimos da lista se estiver ASC.
            # Verificação feita em 'check_sorting.py': Bids ASC, Asks ASC.
            # Então Best Bid é bids[-1], Best Ask é asks[0].
            
            # Ajuste de slicing para pegar os 10 melhores
            top_bids = bids[-10:] # Os 10 maiores preços de compra
            top_asks = asks[:10]  # Os 10 menores preços de venda

            bid_vol = 0.0
            ask_vol = 0.0

            # Cálculo de Volume com Detecção de Spoofing Simples
            # Se uma ordem for > 50% do volume total do bloco, reduz seu peso pela metade.
            
            raw_bid_vols = [float(x[1]) for x in top_bids]
            raw_ask_vols = [float(x[1]) for x in top_asks]
            
            total_raw_bid = sum(raw_bid_vols)
            total_raw_ask = sum(raw_ask_vols)

            for vol in raw_bid_vols:
                if detect_spoofing and total_raw_bid > 0 and (vol / total_raw_bid) > 0.5:
                    bid_vol += vol * 0.5 # Penaliza baleia estática
                else:
                    bid_vol += vol

            for vol in raw_ask_vols:
                if detect_spoofing and total_raw_ask > 0 and (vol / total_raw_ask) > 0.5:
                    ask_vol += vol * 0.5 # Penaliza baleia estática
                else:
                    ask_vol += vol

            total_vol = bid_vol + ask_vol

            if total_vol == 0:
                return 0.0

            obi = (bid_vol - ask_vol) / total_vol
            return obi
        except Exception as e:
            self.logger.error(f"Erro ao calcular OBI: {e}")
            return 0.0

    def get_smart_entry_price(self, symbol, side):
        """
        Calcula o preço de entrada inteligente baseado no Order Book.
        Objetivo: Execução Maker (PostOnly) com alta probabilidade de preenchimento.
        
        Lógica:
        1. Analisa Spread e OBI.
        2. Se Spread largo (> 2 ticks), faz Front-Running do Best Bid/Ask (+1 tick).
        3. Se Spread justo, cola no Best Bid/Ask.
        4. Se OBI muito forte a favor, considera pagar spread (se permitido, mas aqui focamos em Maker).
        
        Returns:
            price (float): Preço sugerido.
            reason (str): Lógica utilizada.
        """
        try:
            depth = self.data.get_orderbook_depth(symbol)
            if not depth:
                return 0.0, "Sem dados de Depth"
                
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            
            if not bids or not asks:
                return 0.0, "Book vazio"

            # Best Bid = Último da lista (Preço Mais Alto)
            best_bid_price = float(bids[-1][0])
            # Best Ask = Primeiro da lista (Preço Mais Baixo)
            best_ask_price = float(asks[0][0])
            
            spread = best_ask_price - best_bid_price
            
            # Tick Size estimado (pode ser refinado buscando infos do ativo)
            # Assumindo precisão baseada no preço atual
            import math
            if best_bid_price > 1000: tick_size = 0.1
            elif best_bid_price > 1: tick_size = 0.01
            elif best_bid_price > 0.01: tick_size = 0.0001
            else: tick_size = 0.000001
            
            spread_ticks = spread / tick_size
            
            obi = self.calculate_obi(depth)
            
            if side == "Buy":
                # Lógica de Compra
                if spread_ticks > 2:
                    # Spread largo: Front-run do Best Bid para garantir prioridade
                    entry_price = best_bid_price + tick_size
                    reason = f"Smart Adjust: Front-Running Best Bid (Spread {spread_ticks:.1f} ticks)"
                elif obi > 0.3:
                    # Pressão de Compra: Colar no Best Bid para não perder o bonde
                    entry_price = best_bid_price
                    reason = f"Smart Adjust: Match Best Bid (OBI Bullish {obi:.2f})"
                else:
                    # Mercado neutro/bearish: Tentar pescar um pouco mais baixo
                    entry_price = best_bid_price # - tick_size (Risco de não preencher é alto, mantendo Best Bid por segurança)
                    reason = "Smart Adjust: Match Best Bid (Standard)"
                    
                # Segurança: Nunca comprar acima do Best Ask (Taker)
                if entry_price >= best_ask_price:
                    entry_price = best_bid_price
                    reason = "Smart Adjust: Capped at Best Bid (Avoid Taker)"
                    
                return entry_price, reason

            elif side == "Sell":
                # Lógica de Venda
                if spread_ticks > 2:
                    # Spread largo: Front-run do Best Ask
                    entry_price = best_ask_price - tick_size
                    reason = f"Smart Adjust: Front-Running Best Ask (Spread {spread_ticks:.1f} ticks)"
                elif obi < -0.3:
                    # Pressão de Venda: Colar no Best Ask
                    entry_price = best_ask_price
                    reason = f"Smart Adjust: Match Best Ask (OBI Bearish {obi:.2f})"
                else:
                    entry_price = best_ask_price
                    reason = "Smart Adjust: Match Best Ask (Standard)"
                    
                # Segurança: Nunca vender abaixo do Best Bid (Taker)
                if entry_price <= best_bid_price:
                    entry_price = best_ask_price
                    reason = "Smart Adjust: Capped at Best Ask (Avoid Taker)"
                    
                return entry_price, reason
                
        except Exception as e:
            self.logger.error(f"Erro no Smart Entry: {e}")
            return 0.0, f"Erro: {e}"

    def get_atr(self, symbol, timeframe="15m", length=14):
        """
        Calcula o Average True Range (ATR).
        Requer 'pandas_ta'.
        """
        try:
            klines = self.data.get_klines(symbol, timeframe, limit=length+10)
            if not klines:
                return 0.0
            
            df = pd.DataFrame(klines)
            # Backpack keys: open, high, low, close, volume (check API mapping)
            # Usually: date, open, high, low, close, volume...
            # Garantir colunas float
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            # Calcular ATR usando pandas-ta
            # Se pandas_ta não estiver instalado, fallback para cálculo manual
            try:
                # atr_series = df.ta.atr(length=length) # Desativado
                raise ImportError("pandas_ta disabled")
            except Exception:
                # Manual ATR
                high_low = df['high'] - df['low']
                high_close = (df['high'] - df['close'].shift()).abs()
                low_close = (df['low'] - df['close'].shift()).abs()
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                atr = true_range.rolling(length).mean().iloc[-1]
                return atr

        except Exception as e:
            self.logger.error(f"Erro ao calcular ATR: {e}")
            return 0.0

    def validate_asset_health(self, symbol, side=None):
        """
        História 1: Verifica saúde do ativo.
        Retorna (Aprovado, Motivo, Dados)
        Args:
            symbol (str): Ativo.
            side (str): 'Buy' ou 'Sell' (Opcional). Se fornecido, valida direção.
        """
        context = {}
        
        # 1. OBI Check
        depth = self.data.get_orderbook_depth(symbol)
        obi = self.calculate_obi(depth)
        context['obi'] = obi
        
        # 2. Funding Check
        # Necessita método no data_client para pegar funding
        # Assumindo get_ticker ou get_market_summary
        funding = 0.0
        try:
            markets = self.data.get_mark_prices()
            market_info = next((m for m in markets if m['symbol'] == symbol), None)
            if market_info:
                funding = float(market_info.get('fundingRate', 0))
        except:
            pass
        context['funding'] = funding

        # 3. ATR / Volatilidade Check
        atr = self.get_atr(symbol)
        # Pegar preço atual para calcular %
        try:
            ticker = self.data.get_ticker(symbol)
            current_price = float(ticker['lastPrice'])
            atr_pct = (atr / current_price) if current_price > 0 else 0
        except:
            atr_pct = 0
            
        context['atr_pct'] = atr_pct

        # Regras de Aceite (Specifications.md)
        # Se Side for Buy, OBI não pode ser muito negativo
        if side == "Buy" and obi < -0.3:
            return False, f"Venda Forte Detectada (OBI {obi:.2f} < -0.3). Proibido Long.", context
        
        # Se Side for Sell, OBI não pode ser muito positivo
        if side == "Sell" and obi > 0.3:
            return False, f"Compra Forte Detectada (OBI {obi:.2f} > 0.3). Proibido Short.", context
        
        # Se Side não informado, apenas alerta se for extremo, mas não bloqueia (deixa o executor decidir)
        # Mas mantemos a regra original se não houver side: OBI < -0.3 é perigoso para Long (padrão do mercado é Long bias?)
        # Melhor: Se não tem side, não veta por OBI, pois o executor já checou o sinal.
        
        if funding > 0.0003: # 0.03%
            return False, f"Funding Alto ({funding*100:.4f}% > 0.03%). Crowded Long.", context
            
        if atr_pct < 0.0025: # 0.25% (Ajustado para BTC 0.35%)
            return False, f"Mercado Morto (ATR {atr_pct*100:.3f}% < 0.25%).", context

        return True, "Saúde OK", context

    def get_rsi(self, df, length=14):
        """Calcula RSI manual."""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.rolling(window=length, min_periods=1).mean()
            avg_loss = loss.rolling(window=length, min_periods=1).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0

    def get_bollinger_bands(self, df, length=20, std_dev=2):
        """Calcula Bollinger Bands manual."""
        try:
            sma = df['close'].rolling(window=length).mean()
            std = df['close'].rolling(window=length).std()
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
        except:
            return 0, 0, 0

    def get_volume_intensity(self, symbol):
        """
        Calcula a intensidade do volume (RVOL - Relative Volume).
        Compara o volume da última vela (1m) com a média das últimas 10 velas (1m).
        Retorna um fator (ex: 1.5 = 50% acima da média).
        """
        try:
            # Pega 15 velas de 1m para ter média segura
            klines = self.data.get_klines(symbol, "1m", limit=15)
            if not klines or len(klines) < 10:
                return 1.0 # Sem dados suficientes
            
            df = pd.DataFrame(klines)
            df['volume'] = df['volume'].astype(float)
            
            # Último candle fechado (penúltimo da lista) e atual (último, em formação)
            # Para intensidade REAL, queremos saber o que está acontecendo AGORA.
            # Vamos projetar o volume do candle atual se ele estiver no meio do tempo?
            # Simplificação: Usar os últimos 3 candles fechados vs média dos 10 anteriores.
            
            # Média dos últimos 10 (excluindo o atual em formação)
            avg_vol = df['volume'].iloc[-11:-1].mean()
            
            # Volume atual (último candle fechado para garantir)
            last_vol = df['volume'].iloc[-2] 
            
            if avg_vol <= 0: return 1.0
            
            rvol = last_vol / avg_vol
            return rvol
        except Exception as e:
            self.logger.error(f"Erro Volume Intensity: {e}")
            return 1.0

    def get_smart_money_score(self, symbol):
        """
        Compõe um Score 'Smart Money' (0 a 100) combinando OBI, Volume e Tendência.
        """
        try:
            depth = self.data.get_orderbook_depth(symbol)
            obi = self.calculate_obi(depth)
            rvol = self.get_volume_intensity(symbol)
            
            score = 50 # Neutro
            
            # 1. OBI Impact (+/- 30 pts)
            score += (obi * 30) 
            
            # 2. Volume Booster (Multiplicador de convicção)
            # Se RVOL > 1.5 (Volume 50% maior), amplifica o sinal do OBI
            if rvol > 1.2:
                if obi > 0: score += 10
                elif obi < 0: score -= 10
            
            if rvol > 2.0: # Volume Dobrado (Whale Action?)
                if obi > 0: score += 10
                elif obi < 0: score -= 10
                
            return score, rvol, obi
        except Exception as e:
            self.logger.error(f"Erro Smart Money Score: {e}")
            return 50, 1.0, 0.0

    def get_trend_bias(self, symbol, timeframe="1m", ema_period=50):
        """
        Calcula o viés de tendência no timeframe especificado (ex: 1m).
        Retorna: 'BULLISH', 'BEARISH' ou 'NEUTRAL'.
        """
        try:
            klines = self.data.get_klines(symbol, timeframe, limit=ema_period + 10)
            if not klines or len(klines) < ema_period:
                return "NEUTRAL"
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            
            current_price = df.iloc[-1]['close']
            ema = df['close'].ewm(span=ema_period, adjust=False).mean().iloc[-1]
            
            if current_price > ema:
                return "BULLISH"
            elif current_price < ema:
                return "BEARISH"
            else:
                return "NEUTRAL"
        except Exception as e:
            self.logger.error(f"Erro ao calcular Trend Bias: {e}")
            return "NEUTRAL"

    def get_market_pulse(self):
        """
        ️ MARKET PULSE (Visão 360º)
        Analisa a saúde sistêmica do mercado usando BTC como proxy.
        Retorna: 'BULLISH', 'BEARISH', 'NEUTRAL'
        """
        try:
            # Analisar BTC_USDC_PERP (Rei)
            klines = self.data.get_klines("BTC_USDC_PERP", "15m", limit=20)
            if not klines: return "NEUTRAL"
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            
            current_price = df.iloc[-1]['close']
            ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            
            # Tendência de Curto Prazo (EMA20)
            if current_price < ema_20:
                return "BEARISH"
            elif current_price > ema_20:
                return "BULLISH"
            else:
                return "NEUTRAL"
        except Exception as e:
            self.logger.error(f"Erro no Market Pulse: {e}")
            return "NEUTRAL"
