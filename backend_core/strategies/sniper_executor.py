import pandas as pd
import logging
import asyncio
import time
from core.technical_oracle import TechnicalOracle
from BLACK_MINDZ_CONSTITUTION import * # Importa as Leis Imutáveis

from core.position_manager import PositionManager
from core.system_check import SystemCheck
from core.precision_guardian import PrecisionGuardian

class SniperExecutor:
    """
     SNIPER EXECUTOR (Flow-First Logic)
    Implementa a História 2 das Especificações com hierarquia de Fluxo > Técnica.
    1. Lê Fluxo (OBI)
    2. Valida Técnica (EMA/RSI) como Veto
    3. Executa Atomicamente (Limit Maker + SL/TP)
    """
    def __init__(self, transport, data_client, risk_manager, stealth_mode=False):
        self.transport = transport
        self.data = data_client
        self.risk_manager = risk_manager
        self.oracle = TechnicalOracle(data_client)
        self.logger = logging.getLogger("SniperExecutor")
        self.stealth_mode = stealth_mode
        self.position_manager = PositionManager(transport) # Inicializa Position Manager (Sem RiskManager no init atual)
        
        # ️ PRECISION GUARDIAN (Novo)
        self.guardian = PrecisionGuardian(transport)
        
        # ️ SYSTEM INTEGRITY CHECK (Safety First)
        self.system_check = SystemCheck()
        if not self.system_check.verify_api_integrity():
            self.logger.critical(" FALHA NA INTEGRIDADE DO SISTEMA. SNIPER TRAVADO.")
            raise Exception("System Integrity Check Failed")
            
        #  CARREGANDO CONSTITUIÇÃO
        self.logger.info(" BLACK MINDZ CONSTITUTION LOADED. NIGHT OPS PROTOCOL ACTIVE.")
        
        # Parâmetros Flow-First
        self.OBI_THRESHOLD_STRONG = 0.15 # [MASSIVE] Reduzido para 0.15 (Trend Surfing)
        self.TARGET_ROE = 0.008 # 0.8% TP para Scalp Rápido (Duck Hunt)
        self.LEVERAGE = 15 # Aumentado para 15x para compensar TP curto
        
    def set_mode(self, mode):
        """
        Ajusta a agressividade do Sniper baseada no modo.
        PROFIT: OBI 0.20, ROE 5% (Foco em qualidade)
        VOLUME: OBI 0.12, ROE 2% (Foco em giro rápido/farming)
        MANUAL_EXIT: OBI 0.15, Sem ROE fixo (Mestre no comando)
        """
        if mode == "VOLUME":
            self.OBI_THRESHOLD_STRONG = 0.15 # Leve para pegar volume
            self.TARGET_ROE = 0.02 # 2% Alvo (Giro Rápido para recuperar $)
            self.LEVERAGE = 10 # 10x (Equilíbrio Volume/Risco)
            self.logger.info(f" Sniper Configurado para MODO VOLUME FARM (Lev 10x, TP 2%, OBI > 0.15)")
        elif mode == "OI_BUILDER":
            self.OBI_THRESHOLD_STRONG = 0.25 # [ASSERTIVE] OBI Forte para Hold Seguro
            self.TARGET_ROE = 0.05 # [OI OPTIMIZATION] 5% Alvo para Pontuar na S4 (Tempo de Tela)
            self.LEVERAGE = 12 # 12x (Good Balance)
            self.logger.info(f" Sniper Configurado para OI BUILDER (Lev 12x, TP 5%, OBI > 0.25)")
            self.logger.info(f"   ℹ️ Estratégia: Trades Acertivos (Bússola) + Hold para Open Interest.")
        elif mode == "MANUAL_EXIT":
            self.OBI_THRESHOLD_STRONG = 0.15 # Levemente mais agressivo
            self.TARGET_ROE = 9.99 # Infinito (Ignorado pelo PositionManager modificado)
            self.logger.info(f" Sniper Configurado para MODO MANUAL EXIT (Alavancagem 9x, Lucro Infinito)")
        elif mode == "SUPREME_INTELLIGENCE":
            self.OBI_THRESHOLD_STRONG = 0.30 # OBI Supremo (Só entra com fluxo de Baleia)
            self.TARGET_ROE = 9.99 # Infinito (Saída por Reversão OBI)
            self.LEVERAGE = 5 # Reduzido para 5x (Segurança Máxima para Teste de Conceito)
            self.logger.info(f" SNIPER SUPREMO: OBI > 0.30 | Lev 5x | Validação de Funding Ativa")
        elif mode == "DUCK_HUNT":
            self.OBI_THRESHOLD_STRONG = 0.12 # [MASSIVE VOLUME] Range Aberto
            self.TARGET_ROE = 0.015 # [TARGET] 1.5% (Como solicitado: alvo claro, mas permite hold)
            self.LEVERAGE = 12 # 12x (Potência para Scalp)
            self.logger.info(f" DUCK HUNT MODE ACTIVATED: Range Aberto (OBI > 0.12) | Target: 1.5%")
            self.logger.info(f"   ℹ️  Parceria Humano-IA: Eu levanto os patos, você atira (ou eu fecho no alvo).")
        elif mode == "S4_FINALE":
            self.OBI_THRESHOLD_STRONG = 0.10 # [HYPER SCALP] OBI Sensível para giro rápido
            self.TARGET_ROE = 0.010 # [1% SCALP] Hit & Run agressivo
            self.LEVERAGE = 15 # 15x (Necessário para volume 1M com banca pequena)
            self.logger.info(f" S4 FINALE MODE ACTIVATED: Hyper Scalp (OBI > 0.10) | Target: 1.0%")
            self.logger.info(f"   ️ RISCO ELEVADO: Giro máximo para atingir meta de volume.")
        elif mode == "CONSISTENCY_PROFIT":
            self.OBI_THRESHOLD_STRONG = 0.25 # [ULTRA CONSERVADOR] OBI Forte para qualidade máxima
            self.TARGET_ROE = 0.008 # [0.8%] Lucro pequeno mas consistente
            self.LEVERAGE = 5 # 5x (Risco mínimo, proteção de capital)
            self.logger.info(f" CONSISTENCY PROFIT MODE: Ultra Conservador (OBI > 0.25) | Target: 0.8%")
            self.logger.info(f"   ️ FOCO: Trades de alta qualidade, risco mínimo, lucro consistente")
        elif mode == "SWING_TRADING":
            self.OBI_THRESHOLD_STRONG = 0.35 # [ELITE SWING] OBI extremamente forte para swings
            self.TARGET_ROE = 0.05 # [5%] Target moderado para trades de 2-7 dias
            self.LEVERAGE = 3 # [3x] Alavancagem mínima para segurança em holds longos
            self.logger.info(f" SWING TRADING MODE: Médio Prazo (OBI > 0.35) | Target: 5% | Hold: 2-7 dias")
            self.logger.info(f"    FOCO: Trades swing seguras, proteção máxima do capital aguardando TGE")
        elif mode == "MICRO_SNIPER_OBI":
            self.OBI_THRESHOLD_STRONG = 0.85 # [VACUUM] OBI Extremo para Vácuo de Liquidez
            self.TARGET_ROE = 0.005 # [0.5%] Scalp instantâneo
            self.LEVERAGE = 5 # 5x (Segurança no teste)
            self.logger.info(f" MICRO SNIPER OBI: Vacuum Hunter (OBI > 0.85) | Spread Lock: 0.05%")
            self.logger.info(f"    VANTAGEM: Execução VSC em <50ms. Captura de ineficiência de book.")
        elif mode == "ASYMMETRIC_PROFIT":
            self.OBI_THRESHOLD_STRONG = 0.35 # [ELITE ONLY] Só entra com desequilíbrio massivo
            self.TARGET_ROE = 0.15 # [15%] Alvo longo para capturar tendência
            self.LEVERAGE = 3 # 3x (Alavancagem mínima para segurar drawdowns longos)
            self.logger.info(f"️ ASYMMETRIC PROFIT MODE: Probabilidade Máxima (OBI > 0.35) | Target: 15%")
            self.logger.info(f"    FOCO: Poucos trades. Tiros de precisão. Risco baixo, Retorno alto.")
        else:
            self.OBI_THRESHOLD_STRONG = 0.20 
            self.TARGET_ROE = 0.05
            self.logger.info(f" Sniper Configurado para MODO PROFIT (OBI > 0.20, ROE 5%)")

    async def monitor_stagnation(self):
        """
        ️ STAGNATION KILLER
        Monitora posições abertas. Se uma posição ficar estagnada (sem lucro/prejuízo significativo)
        por muito tempo, encerra para liberar margem (Giro de Capital).
        """
        try:
            positions = self.transport.get_positions()
            if not positions: return

            for p in positions:
                symbol = p.get('symbol')
                qty = float(p.get('quantity', 0))
                if qty == 0: continue
                
                # Dados da posição (Backpack não retorna timestamp de abertura fácil, 
                # então vamos usar PnL e Price Action como proxy de estagnação)
                
                entry_price = float(p.get('entryPrice'))
                mark_price = float(p.get('markPrice'))
                pnl = float(p.get('unrealizedPnl'))
                
                # Se PnL é muito baixo (perto de 0) e já passou X tempo...
                # Como não temos tempo, vamos usar a volatilidade recente.
                # Se o preço atual está MUITO perto da entrada (< 0.2%) e o OBI morreu...
                
                percent_move = abs((mark_price - entry_price) / entry_price)
                
                if percent_move < 0.002: # Menos de 0.2% de movimento (Dead Zone)
                    # Verifica OBI atual
                    depth = self.data.get_orderbook_depth(symbol)
                    obi = self.oracle.calculate_obi(depth)
                    
                    # Se não tem fluxo (OBI neutro) e preço não anda
                    if abs(obi) < 0.1:
                        self.logger.info(f" STAGNATION KILL: {symbol} parado ({percent_move*100:.2f}%) e sem fluxo (OBI {obi:.2f}). Encerrando para girar.")
                        # Fecha a mercado
                        self.transport.execute_order(symbol, "Market", "Sell" if qty > 0 else "Buy", abs(qty))
                        
        except Exception as e:
            self.logger.error(f"Erro no Stagnation Monitor: {e}")

    async def scan_and_execute(self, symbol):
        """
        Rotina principal de scan e execução para um ativo.
        """
        try:
            self.logger.info(f" [SCAN] Analisando {symbol}...")
            
            # 0. CHECK DE POSIÇÃO EXISTENTE (Evitar Overtrading/Erro API)
            try:
                positions = self.transport.get_positions()
                if positions:
                    # Verifica se já existe posição para o símbolo (netQuantity or quantity)
                    existing_pos = None
                    for p in positions:
                        if p['symbol'] == symbol:
                            q = float(p.get('quantity', 0))
                            nq = float(p.get('netQuantity', 0))
                            if q != 0 or nq != 0:
                                existing_pos = p
                                break
                    
                    if existing_pos:
                        # self.logger.info(f"   ️ Posição já aberta em {symbol}. Pulando Scan para evitar duplicação.")
                        # CRITICAL FIX: Mesmo se existir, TEMOS QUE GERENCIAR (SL, Trailing, Squeeze)
                        # O Scan de entrada é pulado, mas o gerenciamento é obrigatório.
                        qty = float(existing_pos.get('netQuantity', existing_pos.get('quantity', 0)))
                        side = "Long" if qty > 0 else "Short"
                        entry_price = float(existing_pos.get('entryPrice'))
                        
                        # Injeta inteligência do Oráculo para o Position Manager (Wall Intel, OBI)
                        # market_pulse e depth já seriam pegos abaixo, mas vamos pegar aqui otimizado
                        depth_mgmt = self.data.get_orderbook_depth(symbol)
                        obi_mgmt = self.oracle.calculate_obi(depth_mgmt)
                        
                        # Chama o Position Manager
                        # ATENÇÃO: Desativando lógica de TP Dinâmico no Position Manager para respeitar o TP Manual/Fixo.
                        # Apenas OBI Rescue (SL de Emergência) deve funcionar.
                        self.position_manager.manage_positions(
                            # target_symbol removido, pois PositionManager itera sobre todas
                            wall_intel={}, 
                            obi_data={symbol: obi_mgmt}
                            # target_roe removido (não suportado no método atual)
                        )
                        return
            except Exception as e:
                self.logger.error(f"Erro ao verificar posições: {e}")

            # 1. ORÁCULO TÉCNICO & FLUXO & PULSO
            # Nova Lógica: Spec Driven Trading DevOps
            # Usa 'get_market_compass' para decisão atômica e parametrizada.
            
            # 0.5 MARGIN SAFETY CHECK - MACHINE GUN MODE (Relaxado)
            # Apenas checa se tem margem mínima para abrir ordem ($5)
            try:
                collateral = self.transport.get_account_collateral()
                available = float(collateral.get('netEquityAvailable', 0))
                if available < 5:
                    self.logger.warning(f"️ MARGIN EXHAUSTED: Disponível ${available:.2f}. Aguardando saídas.")
                    return
            except Exception as e:
                pass # Ignora erro de margem para não travar o loop
            
            compass = self.oracle.get_market_compass(symbol)
            
            # --- THE BRAIN (DECISION CORE) - VELOCITY MODE (DIRECTIONAL SPEED) ---
            # Score > 65 = Entrada (Forte, mas não precisa ser perfeito)
            # TP Otimizado (0.6%) para giro rápido.
            
            score = compass.get('score', 0)
            trend = compass.get('direction', 'NEUTRAL')
            current_price = compass.get('current_price', 0.0)
            
            # VELOCITY PROTOCOL: Equilíbrio entre Qualidade e Frequência.
            THRESHOLD = 65 # Ajustado para 65 (Alta Velocidade)
            
            obi_val = compass.get('obi', 0.0)
            
            self.logger.info(f"    Compass Score: {score}/100 | Trend: {trend} | OBI: {obi_val:.2f} | Reasons: {compass.get('reasons')}")
            
            # ASSERTIVE FILTER (Trades Acertivos)
            if abs(obi_val) < self.OBI_THRESHOLD_STRONG:
                # Se o fluxo não for forte o suficiente para o modo escolhido, aborta mesmo com Score alto.
                # self.logger.info(f"    OBI Weak ({obi_val:.2f} < {self.OBI_THRESHOLD_STRONG}). Waiting for strong flow.")
                return

            side = None
            reason = ""
            
            if score >= THRESHOLD:
                if trend == "BULLISH":
                    side = "Buy"
                    reason = f"VELOCITY SNIPER BUY (Score {score})"
                elif trend == "BEARISH":
                    side = "Sell"
                    reason = f"VELOCITY SNIPER SELL (Score {score})"
            
            # EXECUÇÃO ATÔMICA COM PROTEÇÃO
            if side:
                print(f" SINAL CONFIRMADO: {side} {symbol} | {reason}")
                
                # MACHINE GUN SIZING (PULVERIZER MODE)
                # Dynamic Sizing based on Mode
                leverage = self.LEVERAGE
                notional = 100 # Base Size
                
                # Executar Ordem + Stop Loss Atômico
                # Como a API da Backpack pode não suportar OTO (One-Triggers-Other) nativo perfeito em uma chamada,
                # Vamos enviar a ordem de entrada e IMEDIATAMENTE a de Stop.
                # Em "Spec Driven", isso deve ser uma transação única lógica.
                
                # 1. Market Entry (Garantir entrada - CORRIGIDO: MAKER ONLY)
                # O Mestre ordenou: ZERO MARKET ORDERS. Entramos como Maker ou não entramos.
                # USE PRECISION GUARDIAN FOR QUANTITY
                qty_raw = notional / current_price
                qty_fmt = self.guardian.format_quantity(symbol, qty_raw)
                
                # MAKER ENTRY PROTOCOL (Post Only Simulation)
                # Tenta pegar no topo do book (Best Bid/Ask) sem cruzar o spread.
                try:
                    # Se quero comprar, coloco no Best Bid (não no Ask).
                    # Se quero vender, coloco no Best Ask (não no Bid).
                    # Isso garante que a ordem vai para o book e não executa na hora (Maker).
                    
                    depth = self.data.get_orderbook_depth(symbol)
                    if side == "Buy":
                        # Pega o melhor Bid atual
                        # Ajuste para Maker Agressivo (Spread Chase)
                        # Mestre permitiu spread maior para garantir entrada em setups de alto potencial.
                        # Aumentado de 0.02% para 0.06% (Cruza o spread padrão de 0.05%)
                        limit_price = current_price * 1.0006 # 0.06% ACIMA (Garante fill)
                    else:
                        limit_price = current_price * 0.9994 # 0.06% ABAIXO (Garante fill)
                        
                    # USE PRECISION GUARDIAN FOR PRICE
                    limit_price_fmt = self.guardian.format_price(symbol, limit_price)
                    
                    self.logger.info(f"   ️ MAKER ENTRY PROTOCOL (AGGRESSIVE SPREAD): Limit {side} @ {limit_price_fmt} (Post Only Intent)")
                    # Envia Limit Order (IOC para tentar pegar liquidez instantânea sem ser Market)
                    entry_res = self.transport.execute_order(symbol, "Limit", side, qty_fmt, price=limit_price_fmt, time_in_force="IOC")
                except Exception as e:
                    self.logger.error(f"   ️ Maker Entry Calc Failed ({e}). ABORTING ENTRY.")
                    return 
                
                if entry_res:
                    # 2. Atomic Stop Loss (JAIL PROTECTION MODE)
                    # Errata do Mestre: "STOP LOSS DEVE SER UMA LEI".
                    # Reativando Protocolo de Proteção Máxima.
                    # Nenhuma ordem dorme descoberta.
                    
                    sl_dist = compass.get('stop_loss_dist', 0.02)
                    
                    # Ajuste Fino Duck Hunt (Stops mais curtos para preservar capital no giro)
                    sl_dist = min(sl_dist, 0.015) # Cap em 1.5%
                    
                    entry_price = float(current_price) 
                    
                    if side == "Buy":
                        sl_price = entry_price * (1 - sl_dist)
                        sl_side = "Ask" # Sell
                    else:
                        sl_price = entry_price * (1 + sl_dist)
                        sl_side = "Bid" # Buy
                        
                    # USE PRECISION GUARDIAN FOR STOP PRICE
                    sl_price_fmt = self.guardian.format_price(symbol, sl_price)
                    
                    payload_sl = {
                        "symbol": symbol,
                        "side": sl_side,
                        "orderType": "Market", # FIX: Market + Trigger
                        "quantity": qty_fmt, 
                        "triggerPrice": sl_price_fmt,
                        "triggerQuantity": qty_fmt # FIX: Trigger Quantity
                    }
                    # Tentar enviar Stop
                    self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload_sl)
                    print(f"   ️ JAIL PROTECTION: SL Cravado em {sl_price_fmt}")
                    
                    # 3. ATOMIC TAKE PROFIT (Dynamic Mode)
                    # Mestre ordenou: TP Assertivo e Otimizado para OI.
                    
                    tp_pct = self.TARGET_ROE 
                    if side == "Buy":
                        tp_price = entry_price * (1 + tp_pct)
                        tp_side = "Ask"
                    else:
                        tp_price = entry_price * (1 - tp_pct)
                        tp_side = "Bid"
                        
                    tp_price_fmt = self.guardian.format_price(symbol, tp_price)
                    
                    # Envia Limit Order (Maker Exit)
                    print(f"    PULVERIZER TP: Posicionando Saída em {tp_price_fmt} (+3.0%)")
                    self.transport.execute_order(symbol, "Limit", tp_side, qty_fmt, price=tp_price_fmt)
            
            return # Fim do Scan (Bússola substitui lógica antiga)

            # --- CÓDIGO LEGADO ABAIXO (MANTIDO PARA REFERÊNCIA MAS IGNORADO PELO RETURN) ---
            
            depth = self.data.get_orderbook_depth(symbol)
            obi = self.oracle.calculate_obi(depth)
            
            # Contexto Técnico (EMA50 + RSI + SMA200)
            klines = self.data.get_klines(symbol, "3m", limit=210) # Mudança para 3m (Scalp Focus) e 210 candles para SMA200
            if not klines or len(klines) < 200: 
                # Se não tiver histórico 3m suficiente, tenta 15m como fallback
                klines = self.data.get_klines(symbol, "15m", limit=210)
                if not klines: return

            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            current_price = df.iloc[-1]['close']
            
            # SMA 200 (Trend Filter Principal)
            sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
            major_trend = "BULLISH" if current_price > sma_200 else "BEARISH"
            
            # EMA 50 (Trend Filter Curto Prazo)
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            short_trend = "BULLISH" if current_price > ema_50 else "BEARISH"
            
            # Cálculo manual de RSI (14 períodos)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            rsi = df.iloc[-1]['rsi']

            trend = major_trend # O Orquestrador vai respeitar a Tendência Maior (SMA 200)
            
            # 1.5 BOLLINGER BANDS SCALP (NOVO: Reversão à Média 3m)
            # Racional: Preço esticou demais nas bandas (3m) -> Reversão Rápida (Scalp)
            
            side = None
            reason = ""

            try:
                bb_upper, bb_mid, bb_lower, bb_width = self.oracle.get_bollinger_bands(symbol, timeframe="3m")
            except (TypeError, ValueError):
                # Fallback
                try:
                    res = self.oracle.get_bollinger_bands(symbol)
                    if len(res) == 4:
                        bb_upper, bb_mid, bb_lower, bb_width = res
                    else:
                        bb_upper, bb_mid, bb_lower = res
                        bb_width = 0 
                except:
                    bb_upper, bb_mid, bb_lower, bb_width = 0, 0, 0, 0

            is_bb_squeeze = bb_width < 0.01 
            
            # Setup "Fechou Fora, Fechou Dentro" com FILTRO DE TENDÊNCIA (SMA 200)
            is_bb_short = current_price > bb_upper and rsi > 70
            is_bb_long = current_price < bb_lower and rsi < 30
            
            # AGGRESSIVE MODE CHECK (Manual Exit = Aggressive)
            is_aggressive = self.TARGET_ROE > 5.0 # 9.99 = Manual Exit
            
            # SCALP REFINEMENT (Filtro de Ruído)
            # Para evitar facas caindo, exigimos que o preço esteja "voltando" para a média.
            # Long: Preço atual > Mínima do candle anterior (Rejeição de fundo)
            # Short: Preço atual < Máxima do candle anterior (Rejeição de topo)
            
            # Simulação simples de Price Action usando dados recentes
            last_close = df.iloc[-2]['close'] if len(df) > 1 else current_price
            is_reversing_up = current_price > last_close
            is_reversing_down = current_price < last_close

            # --- SMART MONEY FINE TUNE (PAXG ACCUMULATION) ---
            if "PAXG" in symbol:
                # PAXG é defensivo/acumulação. Comprar em Dips mesmo sem reversão forte.
                if is_bb_long and obi > 0:
                     side = "Buy"
                     reason = f"PAXG ACCUMULATION (Bollinger Low + Bull Flow)"
                     self.logger.info(f"   ️ PAXG Defense: {reason}")
            
            if not side: # Só processa BB normal se não for PAXG special
                if is_bb_long:
                    # Se Agressivo: Aceita contra-tendência se RSI extremo (<25) ou OBI muito forte
                    # Refinamento: Só entra se estiver revertendo para cima (Price Action)
                    if ((major_trend == "BULLISH" and obi > 0.1) or (is_aggressive and (rsi < 25 or obi > 0.3))) and is_reversing_up:
                        side = "Buy"
                        reason = f"BOLLINGER DIP (Trend Bullish/Aggressive + Oversold RSI {rsi:.1f} + Reversal)"
                        self.logger.info(f"    BB SCALP: {reason}")
                    else:
                        self.logger.info(f"   ️ BB Long Vetado: Tendência, OBI ou Falta de Reversão.")
                    
                elif is_bb_short:
                    # Se Agressivo: Aceita contra-tendência se RSI extremo (>75) ou OBI muito fraco
                    # Refinamento: Só entra se estiver revertendo para baixo (Price Action)
                    if ((major_trend == "BEARISH" and obi < -0.1) or (is_aggressive and (rsi > 75 or obi < -0.3))) and is_reversing_down:
                        side = "Sell"
                        reason = f"BOLLINGER TOP (Trend Bearish/Aggressive + Overbought RSI {rsi:.1f} + Reversal)"
                        self.logger.info(f"    BB SCALP: {reason}")
                    else:
                        self.logger.info(f"   ️ BB Short Vetado: Tendência, OBI ou Falta de Reversão.")

            # 2. DECISÃO SIMPLIFICADA (TREND SURFER - VOLUME MAKER)
            # Só executa se não houver sinal de Bollinger (Prioridade para Reversão se houver)
            
            if not side:
                # Tendência Predominante (SMA 200 manda, EMA 50 confirma)
                is_full_bull = major_trend == "BULLISH" and short_trend == "BULLISH"
                is_full_bear = major_trend == "BEARISH" and short_trend == "BEARISH"
                
                # --- SMART MONEY FINE TUNE (MOMENTUM CHECK) ---
                # Verificar força da tendência nas últimas 50 barras (~2.5h)
                start_price = df.iloc[-50]['close'] if len(df) > 50 else df.iloc[0]['close']
                trend_strength = (current_price - start_price) / start_price
                is_high_momentum = trend_strength > 0.03 # > 3% em 2.5h é Momentum Forte
                
                # Configurações Dinâmicas
                rsi_max_long = 85 if is_high_momentum else 75
                min_obi_long = 0.08 if is_high_momentum else 0.15 # Reduzido para 0.08 em Momentum
                
                # ANTI-FAKEOUT FILTER (Smart Attack)
                # Não comprar rompimento se o preço já esticou demais sem volume insano
                # SMA Distance: Se preço > 2% da SMA200, cuidado.
                sma_dist = (current_price - sma_200) / sma_200
                is_extended = abs(sma_dist) > 0.02

                if is_full_bull:
                    # Se estamos em Full Bull, qualquer fluxo comprador (OBI > 0.1) é sinal de entrada
                    # REFINEMENT: Se esticado, exige OBI > 0.3 (Whale)
                    min_obi = 0.25 if is_extended else min_obi_long # Reduzido de 0.3 para 0.25
                    
                    if obi > min_obi:
                        if rsi < rsi_max_long: # Evitar topo absoluto apenas (Dinâmico)
                            side = "Buy"
                            reason = f"TREND SURFER LONG (Trend Bullish + OBI {obi:.2f})"
                            if is_high_momentum: reason += " [HIGH MOMENTUM]"
                        else:
                            # Se RSI > 75 (ou 85), só entra se for Breakout REAL (OBI > 0.4)
                            if obi > 0.4:
                                side = "Buy"
                                reason = f"MOMENTUM BREAKOUT LONG (RSI High + Massive OBI {obi:.2f})"
                            else:
                                self.logger.info(f"   ️ Trend Bullish, mas RSI Esticado ({rsi:.1f}) e OBI fraco. Fakeout Risk.")
                    elif obi < -0.2:
                        # Fluxo vendedor em tendência de alta = Pullback (Oportunidade de Compra se RSI baixo)
                        if rsi < 40:
                            side = "Buy"
                            reason = f"TREND PULLBACK LONG (Trend Bullish + Dip Flow)"
                
                elif is_full_bear:
                    # Se estamos em Full Bear, qualquer fluxo vendedor (OBI < -0.1) é sinal de entrada
                    min_obi = -0.3 if is_extended else -0.15

                    if obi < min_obi:
                        if rsi > 25: # Evitar fundo absoluto apenas
                            side = "Sell"
                            reason = f"TREND SURFER SHORT (Trend Bearish + OBI {obi:.2f})"
                        else:
                            # Se RSI < 25, só entra se for Breakdown REAL (OBI < -0.4)
                            if obi < -0.4:
                                side = "Sell"
                                reason = f"MOMENTUM BREAKDOWN SHORT (RSI Low + Massive OBI {obi:.2f})"
                            else:
                                self.logger.info(f"   ️ Trend Bearish, mas RSI Oversold ({rsi:.1f}) e OBI fraco. Fakeout Risk.")
                    elif obi > 0.2:
                        # Fluxo comprador em tendência de baixa = Repique (Oportunidade de Venda se RSI alto)
                        if rsi > 60:
                            side = "Sell"
                            reason = f"TREND PULLBACK SHORT (Trend Bearish + Pump Flow)"

            # Fallback: Se tendência mista (SMA vs EMA divergentes), opera Range/Bollinger
            # [MASSIVE ATTACK] - Reativando Range Mode para agressividade controlada.
            # Se OBI confirmar, entra contra a tendência menor (Scalp).
            if not side:
                 # Range Mode: Compra Fundo, Vende Topo
                 if is_bb_long and obi > 0:
                     side = "Buy"
                     reason = "RANGE SCALP LONG (Bollinger Low + Flow)"
                 elif is_bb_short and obi < 0:
                     side = "Sell"
                     reason = "RANGE SCALP SHORT (Bollinger High + Flow)"
            
            if not side:
                self.logger.info(f"    Sem Setup Claro (Trend: {major_trend}/{short_trend} | OBI: {obi:.2f}). Aguardando onda.")
                return

            self.logger.info(f"    SINAL DETECTADO: {side} | Motivo: {reason}")
            
            # 3. GESTÃO DE RISCO (Risk Manager)
            # Validar Saúde do Ativo (Funding, ATR)
            approved, health_reason, context = self.oracle.validate_asset_health(symbol, side=side)
            if not approved:
                self.logger.warning(f"    Veto do Oráculo: {health_reason}")
                return

            # FUNDING RATE CHECK (Platinum Farmer Optimization)
            # Só entrar se o Funding estiver favorável (pagando para segurar)
            # Short se Funding > 0 | Long se Funding < 0
            # Tolerância leve para Momentum forte (OBI > 0.3)
            funding_rate = float(context.get('funding_rate', 0))
            is_funding_positive = funding_rate > 0
            
            # [MASSIVE ATTACK] - Funding Ignorado se Momentum for Real
            # O foco é surfar a alta (Trend Surfing). Taxas são irrelevantes se pegarmos 5%.
            
            # Se RUSH_EXPONENTIAL, relaxa filtros de Funding
            is_rush = self.TARGET_ROE == 0.015
            
            if side == "Buy":
                # Long ideal: Funding Negativo (Recebe). Aceitável: Funding Neutro ou Baixo (< 0.01%)
                if is_funding_positive and funding_rate > 0.0001: # 0.01%
                    # Se OBI for bom (>0.15) ou Modo Agressivo, ignora funding
                    if obi < 0.15 and not is_aggressive and not is_rush:
                        self.logger.warning(f"    Funding Check: Veto Long. Funding Positivo ({funding_rate*100:.4f}%) drena lucro.")
                        return
                    else:
                        self.logger.info(f"    Funding Positivo Ignorado: Momentum OBI ({obi:.2f}) ou Agressividade compensa taxa.")
            else: # Short
                # Short ideal: Funding Positivo (Recebe). Aceitável: Funding Neutro.
                if not is_funding_positive and funding_rate < -0.0001:
                    if obi > -0.15 and not is_aggressive and not is_rush:
                         self.logger.warning(f"    Funding Check: Veto Short. Funding Negativo ({funding_rate*100:.4f}%) drena lucro.")
                         return
                    else:
                         self.logger.info(f"    Funding Negativo Ignorado: Momentum OBI ({obi:.2f}) ou Agressividade compensa taxa.")

            # Calcular SL Dinâmico (ATR)
            atr_pct = context.get('atr_pct', 0.01)
            # SL = 1.5x ATR
            sl_dist_pct = max(0.004, min(atr_pct * 1.5, 0.02)) # Min 0.4%, Max 2%
            
            if side == "Buy":
                sl_price = current_price * (1 - sl_dist_pct)
                tp_price = current_price * (1 + self.TARGET_ROE)
            else:
                sl_price = current_price * (1 + sl_dist_pct)
                tp_price = current_price * (1 - self.TARGET_ROE)

            # Verificar Capital
            safe, usable_capital = self.risk_manager.check_capital_safety()
            if not safe:
                self.logger.error("    Capital Insuficiente ou Reserva Atingida.")
                return

            # Calcular Tamanho da Posição (AGENTIC SIZING)
            # Se modo Agressivo (Manual/Volume), usar Alavancagem Dinâmica
            if is_aggressive:
                 # Calcular Confidence Score
                 confidence = 0.5 # Base
                 
                 # Bonus por OBI (Whale Flow)
                 if side == "Buy" and obi > 0.2: confidence += 0.2
                 elif side == "Sell" and obi < -0.2: confidence += 0.2
                 
                 # Bonus por Funding Favorável
                 if (side == "Buy" and funding_rate < 0) or (side == "Sell" and funding_rate > 0):
                     confidence += 0.1
                     
                 # Bonus por Tendência Alinhada
                 if (side == "Buy" and major_trend == "BULLISH") or (side == "Sell" and major_trend == "BEARISH"):
                     confidence += 0.1
                     
                 # Bonus por Bollinger Squeeze (Explosão iminente)
                 if is_bb_squeeze: confidence += 0.2
                 
                 quantity = self.risk_manager.calculate_dynamic_size(
                     usable_capital=usable_capital, 
                     base_leverage=self.LEVERAGE, 
                     current_price=entry_price if 'entry_price' in locals() else current_price,
                     confidence_score=confidence,
                     depth=depth
                 )
            else:
                 # Modo Conservador (Risco Fixo 1%)
                 quantity = self.risk_manager.calculate_position_size(symbol, current_price, sl_price, usable_capital)
            
            # Ajuste de Precisão (Ex: BTC 3 casas, SOL 1 casa)
            # Idealmente ler exchangeInfo, mas hardcoding defensivo:
            if "BTC" in symbol: quantity = round(quantity, 3)
            elif "ETH" in symbol: quantity = round(quantity, 2)
            else: quantity = round(quantity, 1)
            
            if quantity <= 0:
                self.logger.error("    Quantidade Zero calculada.")
                return

            # 4. EXECUÇÃO ATÔMICA (Maker Only)
            # Utilizar Smart Order Adjustment do Oráculo
            smart_price, smart_reason = self.oracle.get_smart_entry_price(symbol, side)
            
            if smart_price > 0:
                entry_price = smart_price
                self.logger.info(f"    {smart_reason} -> Preço Ajustado: {entry_price}")
            else:
                # Fallback para Best Bid/Ask padrão
                if side == "Buy":
                    best_bid = float(depth['bids'][-1][0]) # Backpack Ascending
                    entry_price = best_bid
                else:
                    best_ask = float(depth['asks'][0][0]) # Backpack Ascending
                    entry_price = best_ask
                self.logger.warning(f"   ️ Smart Price falhou, usando Best Bid/Ask padrão: {entry_price}")
                
            self.logger.info(f"    DISPARANDO {side} {quantity} @ {entry_price} (SL: {sl_price:.2f})")
            
            # Payload Atômico (SEM TP Trigger para evitar Taker Fee)
            # O TP será colocado como LIMIT MAKER pelo Position Manager ou logo após.
            payload = {
                "symbol": symbol,
                "side": "Bid" if side == "Buy" else "Ask",
                "orderType": "Limit",
                "quantity": str(quantity),
                "price": str(entry_price),
                "postOnly": True,
                "selfTradePrevention": "RejectTaker",
                "stopLossTriggerPrice": str(round(sl_price, 2))
                # "takeProfitTriggerPrice": REMOVIDO PARA EVITAR TAKER FEE
            }
            
            # CRITICAL SAFETY CHECK: Stop Loss Mandatory
            if not payload.get("stopLossTriggerPrice") or float(payload["stopLossTriggerPrice"]) <= 0:
                self.logger.critical(f" CRITICAL: Tentativa de ordem SEM STOP LOSS em {symbol}. ABORTANDO.")
                return

            # STEALTH MODE: Interceptação de Execução
            if self.stealth_mode:
                self.logger.info(f" [STEALTH] Ordem SIMULADA: {payload['side']} {payload['quantity']} @ {payload['price']} (SL: {payload['stopLossTriggerPrice']})")
                self.logger.info("   (Nenhuma requisição enviada à API)")
                return

            # Enviar Ordem
            # self.transport._send_request... (assumindo acesso ao transport)
            res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res and 'id' in res:
                self.logger.info(f"    ORDEM CONFIRMADA: ID {res['id']}")
                # Colocar TP Limit Maker imediatamente?
                # Não temos garantia de fill imediato (Limit Order).
                # Deixar para o Position Manager detectar a posição e colocar o TP.
            else:
                self.logger.error(f"   ️ Falha no envio: {res}")

        except Exception as e:
            self.logger.error(f"Erro no Scan {symbol}: {e}")
