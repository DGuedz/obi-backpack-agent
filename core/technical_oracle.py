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

    def calculate_obi(self, depth, detect_spoofing=True):
        """
        Calcula o Order Book Imbalance (OBI) com Análise de Profundidade (Multi-Level).
        
        Args:
            depth (dict): Dados do livro de ordens.
            detect_spoofing (bool): Se True, compara Top 1 vs Top 5 para detectar fake walls.
        """
        try:
            if not depth or 'bids' not in depth or 'asks' not in depth:
                return 0.0

            bids = depth.get('bids', [])
            asks = depth.get('asks', [])

            if not bids or not asks:
                return 0.0

            # Backpack Bids are Ascending (Low -> High), Asks are Ascending (Low -> High)
            # Best Bid = bids[-1], Best Ask = asks[0]
            
            # --- 1. Top of Book (L1) ---
            l1_bid_vol = float(bids[-1][1])
            l1_ask_vol = float(asks[0][1])
            
            # --- 2. Deep Book (L5) ---
            # Pegar os 5 melhores níveis
            top5_bids = bids[-5:]
            top5_asks = asks[:5]
            
            l5_bid_vol = sum([float(x[1]) for x in top5_bids])
            l5_ask_vol = sum([float(x[1]) for x in top5_asks])
            
            # --- Spoofing Detection Logic ---
            # Se L1 tem muito volume mas L5 é fraco -> Spoofing (Fake Wall na cara)
            # Se L1 é fraco mas L5 é forte -> Real Pressure (Iceberg/Layering)
            
            # OBI Padrão (Baseado no L5 para robustez)
            total_l5 = l5_bid_vol + l5_ask_vol
            if total_l5 == 0: return 0.0
            
            obi_l5 = (l5_bid_vol - l5_ask_vol) / total_l5
            
            # OBI L1 (Flash Pressure)
            total_l1 = l1_bid_vol + l1_ask_vol
            obi_l1 = (l1_bid_vol - l1_ask_vol) / total_l1 if total_l1 > 0 else 0.0
            
            # --- 3. Micro-Trend Check (Last Traded Price vs Mid) ---
            # Se o último preço (Trade) está batendo no Ask, é pressão de compra agressiva (Taker Buy).
            # Se está batendo no Bid, é pressão de venda agressiva (Taker Sell).
            # Isso valida se o OBI é real ou só ordens passivas.
            
            # Não temos o ticker aqui direto, mas podemos inferir pela proximidade
            # Vamos refinar o OBI com base na agressão do book (L1)
            
            # Weighted OBI Refined:
            # Aumentar peso do L5 para 80% para filtrar spoofing de HFT na cara do book.
            # OBI L1 é muito ruidoso em 0.1s.
            
            final_obi = (obi_l5 * 0.8) + (obi_l1 * 0.2)
            
            # Penalidade de Divergência Extrema (Anti-Trap)
            # Se L1 e L5 discordam totalmente, zera o sinal. É briga de foice.
            if (obi_l1 > 0.3 and obi_l5 < -0.3) or (obi_l1 < -0.3 and obi_l5 > 0.3):
                return 0.0 # Zera sinal (Trap Zone)
                
            return final_obi

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
            elif best_bid_price > 100: tick_size = 0.01
            elif best_bid_price > 10: tick_size = 0.01 # Ajuste para SOL/HYPE (Ex: 22.50)
            elif best_bid_price > 1: tick_size = 0.0001 # Ajuste para LIT/SUI (Ex: 1.5000)
            elif best_bid_price > 0.01: tick_size = 0.0001 # Ajuste para Pennies
            else: tick_size = 0.000001
            
            # Ajuste Fino Específico por Ativo (Hardcoded Wisdom)
            if "SOL" in symbol: tick_size = 0.01
            elif "HYPE" in symbol: tick_size = 0.001 # Hype tem 3 casas decimais muitas vezes
            elif "BTC" in symbol: tick_size = 0.1
            elif "ETH" in symbol: tick_size = 0.01
            
            spread_ticks = spread / tick_size
            
            obi = self.calculate_obi(depth)
            
            if side == "Buy":
                # Lógica de Compra Maker Agressiva (Zero Fee Hunt)
                if spread_ticks > 1.5:
                    # Spread existe: Front-run do Best Bid (+1 tick)
                    entry_price = best_bid_price + tick_size
                    reason = f"Smart Adjust: Front-Running Best Bid (Spread {spread_ticks:.1f} ticks)"
                elif obi > 0.2:
                    # Pressão de Compra: Colar no Best Bid
                    entry_price = best_bid_price
                    reason = f"Smart Adjust: Match Best Bid (OBI Bullish {obi:.2f})"
                else:
                    # Mercado neutro/bearish: Tentar pescar no Best Bid mesmo
                    entry_price = best_bid_price
                    reason = "Smart Adjust: Match Best Bid (Standard)"
                    
                # Segurança Final: Nunca cruzar o spread (Taker)
                # Se entry_price >= Best Ask, recua para Best Ask - 1 tick (ou Best Bid)
                if entry_price >= best_ask_price:
                    entry_price = best_ask_price - tick_size
                    reason = "Smart Adjust: Capped below Best Ask (Avoid Taker)"
                    
                return entry_price, reason

            elif side == "Sell":
                # Lógica de Venda Maker Agressiva (Zero Fee Hunt)
                if spread_ticks > 1.5:
                    # Spread existe: Front-run do Best Ask (-1 tick)
                    entry_price = best_ask_price - tick_size
                    reason = f"Smart Adjust: Front-Running Best Ask (Spread {spread_ticks:.1f} ticks)"
                elif obi < -0.2:
                    # Pressão de Venda: Colar no Best Ask
                    entry_price = best_ask_price
                    reason = f"Smart Adjust: Match Best Ask (OBI Bearish {obi:.2f})"
                else:
                    entry_price = best_ask_price
                    reason = "Smart Adjust: Match Best Ask (Standard)"
                    
                # Segurança Final: Nunca cruzar o spread (Taker)
                if entry_price <= best_bid_price:
                    entry_price = best_bid_price + tick_size
                    reason = "Smart Adjust: Capped above Best Bid (Avoid Taker)"
                    
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

    def get_bollinger_bands(self, symbol, timeframe="3m", period=20, std_dev=2.0):
        """
        Calcula as Bandas de Bollinger (SMA 20 + 2 StdDev).
        Usado para estratégia de reversão à média (Mean Reversion).
        
        Returns:
            upper (float)
            mid (float)
            lower (float)
            bandwidth (float): (Upper - Lower) / Mid
        """
        try:
            klines = self.data.get_klines(symbol, timeframe, limit=period+5)
            if not klines: return 0,0,0,0
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            
            # Cálculo Manual
            sma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            current_upper = upper.iloc[-1]
            current_lower = lower.iloc[-1]
            current_mid = sma.iloc[-1]
            
            if current_mid == 0: return 0,0,0,0
            
            bandwidth = (current_upper - current_lower) / current_mid
            
            return current_upper, current_mid, current_lower, bandwidth
            
        except Exception as e:
            self.logger.error(f"Erro BB: {e}")
            return 0,0,0,0

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
        # VERSÃO SIMPLIFICADA (TREND SURFER)
        # Se Side for Buy, OBI não pode ser extremamente negativo (Falling Knife)
        if side == "Buy" and obi < -0.4: # Aumentado de -0.3 para -0.4 (Mais tolerância para Pullbacks)
            return False, f"Venda Forte Detectada (OBI {obi:.2f} < -0.4). Proibido Long (Falling Knife).", context
        
        # Se Side for Sell, OBI não pode ser extremamente positivo (Rocket Launch)
        if side == "Sell" and obi > 0.4: # Aumentado de 0.3 para 0.4
             return False, f"Compra Forte Detectada (OBI {obi:.2f} > 0.4). Proibido Short (Squeeze Risk).", context
        
        # Se Side não informado, apenas alerta se for extremo, mas não bloqueia (deixa o executor decidir)
        
        return True, "Aprovado pelo Oráculo (Trend Surfer Mode).", context

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

    def get_market_compass(self, symbol):
        """
         BÚSSOLA DE MILISSEGUNDOS (Market Compass)
        Agrega múltiplos sinais para gerar um 'Score de Certeza' (0-100) e parâmetros de risco.
        
        Componentes:
        1. BTC Trend (Macro): O Rei dita a direção.
        2. OBI (Micro): O Fluxo dita o timing.
        3. Volatilidade (ATR): O Medo dita o tamanho da mão e o Stop.
        4. Spread/Liquidez: A Eficiência dita o custo.
        
        Returns:
            dict: {
                'score': int (0-100),
                'direction': 'BULLISH'/'BEARISH'/'NEUTRAL',
                'volatility_risk': 'LOW'/'MEDIUM'/'HIGH',
                'suggested_leverage': int,
                'stop_loss_dist': float, # % de distância
                'reasons': list
            }
        """
        compass = {
            'score': 50,
            'direction': 'NEUTRAL',
            'volatility_risk': 'MEDIUM',
            'suggested_leverage': 1,
            'stop_loss_dist': 0.05,
            'current_price': 0.0,
            'reasons': []
        }
        
        try:
            # 1. BTC Trend (Macro Check)
            # Se BTC estiver caindo forte, Score de Long diminui drasticamente.
            btc_klines = self.data.get_klines("BTC_USDC_PERP", "15m", limit=50)
            if btc_klines:
                btc_df = pd.DataFrame(btc_klines)
                btc_df['close'] = btc_df['close'].astype(float)
                btc_sma20 = btc_df['close'].rolling(window=20).mean().iloc[-1]
                btc_price = btc_df['close'].iloc[-1]
                
                btc_trend = "BULLISH" if btc_price > btc_sma20 else "BEARISH"
                compass['reasons'].append(f"BTC Trend: {btc_trend}")
            else:
                btc_trend = "NEUTRAL"

            # 2. Asset Specifics
            depth = self.data.get_orderbook_depth(symbol)
            obi = self.calculate_obi(depth)
            
            klines = self.data.get_klines(symbol, "15m", limit=210)
            if not klines: return compass
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            price = df['close'].iloc[-1]
            sma200 = df['close'].rolling(window=200).mean().iloc[-1]
            
            # Trend Check (The Shield)
            trend = "BULLISH" if price > sma200 else "BEARISH"
            compass['direction'] = trend
            compass['current_price'] = price
            
            # 3. Spread & Liquidity Gate (The Wall)
            best_bid = float(depth['bids'][-1][0]) if depth['bids'] else 0
            best_ask = float(depth['asks'][0][0]) if depth['asks'] else float('inf')
            spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 1.0
            
            compass['reasons'].append(f"Spread: {spread*100:.3f}%")
            
            if spread > 0.0015: # Spread > 0.15% é inaceitável para Scalp
                compass['score'] = 0
                compass['reasons'].append(" SPREAD TOO HIGH (Kill Switch)")
                return compass
            
            # Volatility (ATR)
            atr = self.get_atr(symbol)
            atr_pct = (atr / price) if price > 0 else 0.01
            
            # Risk Classification
            if atr_pct > 0.02: # > 2% Volatilidade em 15m
                compass['volatility_risk'] = 'HIGH'
                compass['stop_loss_dist'] = atr_pct * 2.5 # Stop largo (2.5x ATR)
                compass['suggested_leverage'] = 3
            elif atr_pct > 0.01:
                compass['volatility_risk'] = 'MEDIUM'
                compass['stop_loss_dist'] = atr_pct * 2.0 # Stop médio (2.0x ATR)
                compass['suggested_leverage'] = 5
            else:
                compass['volatility_risk'] = 'LOW'
                compass['stop_loss_dist'] = max(0.01, atr_pct * 1.5) # Stop curto mas seguro
                compass['suggested_leverage'] = 9 # Alavancagem agressiva apenas em calmaria
                
            # SCORING ALGORITHM (Scalp / Volume Focus)
            score = 50
            
            # 1. SCALP SETUP (Reversão à Média 3m) - Prioridade
            # Verifica se preço está esticado no curto prazo
            try:
                # Need faster data for scalp check
                klines_3m = self.data.get_klines(symbol, "3m", limit=20)
                if klines_3m:
                    df_3m = pd.DataFrame(klines_3m)
                    df_3m['close'] = df_3m['close'].astype(float)
                    last_price = df_3m.iloc[-1]['close']
                    ema_20_3m = df_3m['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    
                    # Distância da Média
                    dist_pct = (last_price - ema_20_3m) / ema_20_3m
                    
                    # Se preço esticou muito para baixo (-1%) e OBI positivo -> COMPRA (Scalp de Repique)
                    if dist_pct < -0.01 and obi > 0.15:
                        score += 40
                        compass['direction'] = "BULLISH" # Override Trend Macro for Scalp
                        compass['reasons'].append("Scalp: Oversold + Flow")
                    
                    # Se preço esticou muito para cima (+1%) e OBI negativo -> VENDA (Scalp de Correção)
                    elif dist_pct > 0.01 and obi < -0.15:
                        score += 40
                        compass['direction'] = "BEARISH" # Override Trend Macro for Scalp
                        compass['reasons'].append("Scalp: Overbought + Flow")
            except Exception:
                pass

            # 2. Trend Alignment (+20) - Peso Reduzido
            if trend == btc_trend: score += 20
            else: score -= 10 
            
            # 3. OBI Alignment (+30) - Peso Aumentado (Flow First)
            # Se OBI for muito forte, justifica entrada
            if obi > 0.25:
                score += 30
                if trend == "BEARISH": compass['reasons'].append("Flow Override: Strong Buy")
            elif obi < -0.25:
                score += 30
                if trend == "BULLISH": compass['reasons'].append("Flow Override: Strong Sell")
            elif (trend == "BULLISH" and obi > 0.05) or (trend == "BEARISH" and obi < -0.05):
                score += 10
                
            # Volatility Penalty
            if compass['volatility_risk'] == 'HIGH': score -= 10
            
            compass['score'] = max(0, min(100, score))
            compass['reasons'].append(f"Asset Trend: {trend} (SMA200)")
            compass['reasons'].append(f"OBI: {obi:.2f}")
            compass['reasons'].append(f"Vol: {atr_pct*100:.2f}% ({compass['volatility_risk']})")
            compass['obi'] = obi
            
            return compass
            
        except Exception as e:
            self.logger.error(f"Erro na Bússola: {e}")
            return compass

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
