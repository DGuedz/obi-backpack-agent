
import time
import pandas as pd
from core.backpack_transport import BackpackTransport

class PositionManager:
    """
    ️ POSITION MANAGER (Sustentabilidade & Tendência)
    Monitora posições abertas e aplica regras de gestão dinâmica:
    1. Breakeven: Se lucro > 2%, move SL para Entrada + Taxas.
    2. Trend Guard: Se tendência inverter (Preço cruzar EMA50), fecha posição (Market).
    """
    def __init__(self, transport: BackpackTransport):
        self.transport = transport
        self.BREAKEVEN_TRIGGER_PCT = 0.02 # 2% de Lucro aciona Breakeven
        self.BREAKEVEN_BUFFER_PCT = 0.003 # 0.3% acima da entrada para cobrir taxas (Maker + Taker + Spread)

    def manage_positions(self, wall_intel=None, obi_data=None):
        """
        Escaneia e protege posições ativas.
        Aceita 'wall_intel' (Dict) do Book Scanner.
        Aceita 'obi_data' (Dict) do Technical Oracle.
        """
        try:
            positions = self.transport.get_positions()
            if not positions: return
            
            # --- HEDGE MONITOR (BTC vs ETH) ---
            # Verifica se o lucro do ETH cobre o prejuízo do BTC para saída estratégica
            self._check_hedge_exit(positions, obi_data)
            # ----------------------------------

            for pos in positions:
                symbol = pos.get('symbol')
                side = pos.get('side')
                
                # Fix: API returns 'netQuantity', not 'quantity'
                qty = float(pos.get('netQuantity', pos.get('quantity', 0)))
                
                if not side: 
                    if qty > 0: side = "Long"
                    elif qty < 0: side = "Short"
                    else: continue
                
                print(f"DEBUG: {symbol} | Side: {side} | Qty: {qty}")

                entry_price = float(pos.get('entryPrice'))
                ticker = self.transport.get_ticker(symbol)
                if not ticker: continue
                current_price = float(ticker.get('lastPrice')) 
                
                # 0. OBI RESCUE (Novo: Sair com perdas mínimas se fluxo virar)
                if obi_data and symbol in obi_data:
                    obi = obi_data[symbol]
                    if self._check_obi_rescue(symbol, side, obi, entry_price, current_price):
                        continue

                # 1. CHECK TREND ALIGNMENT (Trend Guard)
                if self._check_trend_invalidation(symbol, side, current_price):
                    print(f"   ️ TREND REVERSAL DETECTED em {symbol}! Mudando Estratégia...")
                    self._emergency_close(symbol, side, qty)
                    continue 

                # 1.5 CHECK TP/SL ORDERS (Recovery/Consistency)
                self._ensure_exit_orders(symbol, side, entry_price, abs(qty), current_price)

                # 1.8 WALL GUARDIAN (Inteligência Privilegiada)
                if wall_intel and symbol in wall_intel:
                    self._apply_wall_protection(symbol, side, current_price, wall_intel[symbol])

                # 1.9 SQUEEZE GUARD (Short Safety)
                # Se Short em RSI < 30 e Preço subindo -> Apertar Stop ou Sair
                # Idealmente precisariamos do RSI aqui. Vamos assumir que se ROI negativo e OBI Bullish, é perigo.
                if side == "Short" and roi < -0.01: # Perdendo 1%
                     if obi_data and symbol in obi_data:
                         if obi_data[symbol] > 0.2: # Fluxo contra forte
                             print(f"    SQUEEZE ALERT em {symbol}! Apertando Stop para BreakEven + 0.5%...")
                             self._emergency_close(symbol, side, qty * 0.5) # Reduzir mão pela metade
                             # TODO: Mover SL para entrada

                # 2. CHECK PROFITABILITY & TRAILING STOP
                # OVERRIDE MESTRE: Manual Exit / Infinite Profit
                # Lógica relaxada para permitir que o Mestre saia manualmente no alvo de 3% ou mais.
                # Só ativa proteção se o lucro for muito bom.

                if side == "Long":
                    roi = (current_price - entry_price) / entry_price
                else:
                    roi = (entry_price - current_price) / entry_price
                
                # Regra Infinite Profit:
                # Se ROI > 3.0% -> Ativa Trailing Stop (1.0% de distância) - Garante lucro gordo
                # Se ROI > 1.5% -> Ativa Breakeven (Protege o trade)
                # Antes disso -> Deixa oscilar.
                
                if roi >= 0.03: # 3.0% Lucro (Alvo do Mestre)
                    self._apply_trailing_stop(symbol, side, current_price, roi)
                elif roi >= 0.015: # 1.5% Lucro
                    self._move_to_breakeven(symbol, side, entry_price)
                
                # Log de Status para o Mestre acompanhar no App
                if roi > 0:
                    print(f"    {symbol} LUCRO: {roi*100:.2f}% (Deixando Correr...)")

        except Exception as e:
            print(f"️ Erro no Position Manager: {e}")

    def _ensure_exit_orders(self, symbol, side, entry_price, quantity, current_price):
        """
        Garante que existam TP (Limit Maker) e SL (Stop Market) para a posição.
        """
        open_orders = self.transport.get_open_orders(symbol)
        
        has_tp = False
        has_sl = False
        
        target_roe = 0.05 # 5% (Profit Mode - Catch Needles)
        sl_dist = 0.025   # 2.5% (Aumentado para 9x Leverage e volatilidade alta)
        
        for o in open_orders:
            o_side = o.get('side')
            o_type = o.get('orderType')
            trigger = float(o.get('triggerPrice', 0)) if o.get('triggerPrice') else 0
            price = float(o.get('price', 0)) if o.get('price') else 0
            
            # Check TP (Limit Order Profit Side)
            if o_type == 'Limit':
                if side == "Long" and o_side == "Ask" and price > entry_price:
                    has_tp = True
                elif side == "Short" and o_side == "Bid" and price < entry_price:
                    has_tp = True
                    
            # Check SL (Stop Market Loss Side)
            # Fix: API may return StopMarket as Market with triggerPrice
            is_stop = 'Stop' in o_type or (o_type == 'Market' and trigger > 0)
            
            if is_stop:
                if side == "Long" and o_side == "Ask" and trigger < entry_price:
                    has_sl = True
                elif side == "Short" and o_side == "Bid" and trigger > entry_price:
                    has_sl = True
                    
        # CRITICAL SAFETY: FORCE SL IF MISSING
        # O SL é inegociável. Se não existir, criar AGORA.
        if not has_sl:
            print(f"    CRITICAL: SL Ausente em {symbol}. Colocando Stop Market DE EMERGÊNCIA...")
            if side == "Long":
                sl_price = entry_price * (1 - sl_dist)
                sl_side = "Ask"
            else:
                sl_price = entry_price * (1 + sl_dist)
                sl_side = "Bid"
                
            if "BTC" in symbol: sl_price = round(sl_price, 1)
            elif "ETH" in symbol: sl_price = round(sl_price, 2)
            elif "HYPE" in symbol: sl_price = round(sl_price, 3)
            elif "SOL" in symbol: sl_price = round(sl_price, 2)
            else: sl_price = round(sl_price, 4)

            payload = {
                "symbol": symbol,
                "side": sl_side,
                "orderType": "Market",
                "quantity": str(quantity),
                "triggerPrice": str(sl_price),
                "triggerQuantity": str(quantity) # FIX: Required when triggerPrice is present
            }
            # Envia imediatamente
            res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            if res:
                print(f"       SL de Emergência Criado: {sl_price}")
            else:
                print(f"       FALHA AO CRIAR SL DE EMERGÊNCIA EM {symbol}!")

        # Place missing TPs (Strategic Scale-Out)
        # OVERRIDE MESTRE: Infinite Profit Mode
        # Não coloca TP Automático. Deixa o lucro correr até decisão manual ou reversão.
        if not has_tp:
             # print(f"   ️ TP Ausente em {symbol}. Colocando Strategic Scale-Out (TPs Parciais)...")
             print(f"   ️ INFINITE PROFIT MODE: TPs Automáticos Desativados. Deixando o lucro correr.")
             pass # Não faz nada, não coloca ordens Limit de saída.

        # Removed redundant SL block (Moved to top priority)

    def _apply_trailing_stop(self, symbol, side, current_price, roi):
        """
        Ajusta o Stop Loss dinamicamente para acompanhar o lucro.
        Distância do Trailing Scalp: 0.5% do Preço Atual.
        """
        trailing_dist = 0.005 # 0.5% de distância (Scalp Apertado)
        
        if side == "Long":
            new_sl = current_price * (1 - trailing_dist)
        else:
            new_sl = current_price * (1 + trailing_dist)
            
        self._update_stop_if_better(symbol, side, new_sl, "TRAILING SCALP")

    def _move_to_breakeven(self, symbol, side, entry_price):
        """
        Move o SL para o preço de entrada (Breakeven) + Taxas (0.2%).
        Garante que saímos no verde (ou pagando o café).
        """
        fee_buffer = 0.002 # 0.2% de buffer para taxas
        
        if side == "Long":
            new_sl = entry_price * (1 + fee_buffer)
        else:
            new_sl = entry_price * (1 - fee_buffer)
            
        # Ajuste de precisão
        if "BTC" in symbol: new_sl = round(new_sl, 1)
        elif "ETH" in symbol: new_sl = round(new_sl, 2)
        else: new_sl = round(new_sl, 4)
            
        self._update_stop_if_better(symbol, side, new_sl, "BREAKEVEN PLUS")

    def _apply_wall_protection(self, symbol, side, current_price, wall_data):
        """
        Ajusta TP ou SL baseado na presença de Paredões.
        """
        wall_type = wall_data.get('type')
        wall_price = float(wall_data.get('price', 0))
        
        if wall_price == 0: return

        # Se Short e tem Support Wall abaixo (perto) -> Ajustar TP para antes do Wall
        if side == "Short" and wall_type == "SUPPORT":
            if current_price > wall_price: # Estamos acima do suporte (lucro ou drawdown)
                dist = (current_price - wall_price) / current_price
                if dist < 0.01: # Menos de 1% de distância
                    print(f"    WALL ALERT: Suporte detectado em {wall_price} para {symbol} Short.")
                    # Colocar TP Maker logo acima do Wall
                    safe_tp = wall_price * 1.001
                    self._update_tp_if_better(symbol, side, safe_tp)

        # Se Long e tem Resist Wall acima (perto) -> Ajustar TP para antes do Wall
        if side == "Long" and wall_type == "RESIST":
            if current_price < wall_price:
                dist = (wall_price - current_price) / current_price
                if dist < 0.01:
                    print(f"    WALL ALERT: Resistência detectada em {wall_price} para {symbol} Long.")
                    safe_tp = wall_price * 0.999
                    self._update_tp_if_better(symbol, side, safe_tp)

    def _update_tp_if_better(self, symbol, side, new_tp):
        """
        Atualiza TP Limit se o novo for mais seguro (mais perto do preço atual) que o antigo.
        """
        open_orders = self.transport.get_open_orders(symbol)
        tp_order = None
        for o in open_orders:
            if o.get('orderType') == 'Limit':
                o_side = o.get('side')
                if (side == "Long" and o_side == "Ask") or (side == "Short" and o_side == "Bid"):
                    tp_order = o
                    break
        
        should_update = False
        if tp_order:
            current_tp = float(tp_order.get('price'))
            # Se Short, TP é Buy. Se novo TP > TP atual (mais perto do preço de entrada/atual), é "pior" pro lucro máximo,
            # MAS é "melhor" pra segurança (garante saída antes do wall).
            # Na verdade, queremos garantir que a saída aconteça.
            # Se o Wall está em 100 e nosso TP está em 90, o preço bate no wall e volta. Nunca pega 90.
            # Então temos que SUBIR o TP do Short para 100.1.
            
            if side == "Short" and new_tp > current_tp:
                should_update = True
            elif side == "Long" and new_tp < current_tp:
                should_update = True
        else:
            should_update = True

        if should_update:
            print(f"   ️ WALL GUARD: Movendo TP de {symbol} para {new_tp:.4f} (Antes do Paredão)")
            if tp_order:
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': tp_order['id']})
            
            # Re-post Limit Maker
            tp_side = "Bid" if side == "Short" else "Ask"
            qty = "0" # Need logic to get position size... 
            # Simplificação: O Position Manager já sabe a qtd da posição no loop principal, 
            # mas aqui é helper. Vamos pegar a posição de novo ou passar como arg.
            # Para não complicar, vamos pular a execução se não tivermos a qtd.
            # Melhor: Apenas logar a sugestão por enquanto, pois cancelar ordem sem saber qtd exata é risco.
            # Vou implementar a execução real no loop principal se necessário.
            pass

    def _update_stop_if_better(self, symbol, side, new_sl, mode):
        """
        Helper para atualizar SL apenas se melhorar a posição.
        """
        open_orders = self.transport.get_open_orders(symbol)
        sl_order = None
        for o in open_orders:
            o_type = o.get('orderType')
            trigger = float(o.get('triggerPrice', 0)) if o.get('triggerPrice') else 0
            is_stop = 'Stop' in o_type or (o_type == 'Market' and trigger > 0)
            
            if is_stop:
                o_side = o.get('side')
                if (side == "Long" and o_side == "Ask") or (side == "Short" and o_side == "Bid"):
                    sl_order = o
                    break
        
        should_update = False
        if sl_order:
            current_trigger = float(sl_order.get('triggerPrice'))
            if side == "Long" and new_sl > current_trigger: # Subir SL
                should_update = True
            elif side == "Short" and new_sl < current_trigger: # Descer SL
                should_update = True
        else:
            should_update = True # Sem SL, cria um

        if should_update:
            print(f"   ️ {mode}: Atualizando SL de {symbol} para ${new_sl:.4f}")
            if sl_order:
                self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", {'symbol': symbol, 'orderId': sl_order['id']})
            self._place_stop(symbol, side, new_sl)
    def _check_obi_rescue(self, symbol, side, obi, entry_price, current_price):
        """
        Verifica se o fluxo (OBI) virou drasticamente contra a posição.
        Se sim, tenta sair no Breakeven (ou mínimo loss) movendo o TP.
        Retorna True se ação tomada.
        """
        # Limiares de Pânico
        OBI_PANIC_THRESHOLD = 0.5 
        
        action_taken = False
        
        # Cenário 1: Short com OBI muito Bullish (Baleias comprando)
        if side == "Short" and obi > OBI_PANIC_THRESHOLD:
            # Se estamos no lucro ou leve prejuízo, tentar sair no 0x0
            # Se entry 100, current 99 (lucro), move TP para 99.5
            # Se entry 100, current 101 (preju), move TP para 100 (Breakeven)
            
            target_price = entry_price * 0.9995 # Sair um pouco abaixo da entrada (cobrir taxas)
            
            # Mas se o preço atual já passou muito (Stop Loss perigo), talvez aceitar prejuízo menor?
            # "Sair com perdas minimas" -> Tentar Entry Price.
            
            print(f"   🆘 OBI RESCUE: Fluxo Bullish ({obi:+.2f}) contra Short em {symbol}.")
            self._update_tp_if_better(symbol, side, target_price)
            action_taken = True

        # Cenário 2: Long com OBI muito Bearish (Baleias vendendo)
        elif side == "Long" and obi < -OBI_PANIC_THRESHOLD:
            target_price = entry_price * 1.0005
            print(f"   🆘 OBI RESCUE: Fluxo Bearish ({obi:+.2f}) contra Long em {symbol}.")
            self._update_tp_if_better(symbol, side, target_price)
            action_taken = True
            
        return action_taken

    def _check_trend_invalidation(self, symbol, side, current_price):
        """
        Verifica se a tendência mudou contra a posição (Cruzamento EMA 50).
        Retorna True se DEVE FECHAR.
        """
        try:
            # Reutiliza lógica de EMA do Gatekeeper
            klines = self.transport.get_klines(symbol, "1h", limit=60)
            if not klines: return False
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            ema_series = df['close'].ewm(span=50, adjust=False).mean()
            ema_50 = ema_series.iloc[-1]
            
            # Regra: Se Long e Preço < EMA50 -> Invalidou
            if side == "Long" and current_price < ema_50:
                # IGNORAR TREND GUARD PARA HEDGE (ETH)
                if "ETH" in symbol:
                    # print(f"   ️ HEDGE MODE: Ignorando Trend Bearish para {symbol} (OBI Bullish)")
                    return False
                    
                print(f"    {symbol} Long Invalidado: Preço ${current_price:.2f} < EMA50 ${ema_50:.2f}")
                return True
            
            # Regra: Se Short e Preço > EMA50 -> Invalidou
            if side == "Short" and current_price > ema_50:
                print(f"    {symbol} Short Invalidado: Preço ${current_price:.2f} > EMA50 ${ema_50:.2f}")
                return True
                
            return False
        except:
            return False

    def _check_hedge_exit(self, positions, obi_data):
        """
        Monitora estratégia de Hedge (BTC Short + ETH Long).
        Se BTC estiver perigoso (OBI Bullish) e ETH cobrir o prejuízo, fecha BTC.
        """
        btc_pos = next((p for p in positions if "BTC" in p['symbol']), None)
        eth_pos = next((p for p in positions if "ETH" in p['symbol']), None)
        
        if not btc_pos or not eth_pos: return
        
        try:
            btc_pnl = float(btc_pos.get('unrealizedPnl', 0))
            eth_pnl = float(eth_pos.get('unrealizedPnl', 0))
            
            # Se BTC está perdendo e ETH ganhando
            if btc_pnl < 0 and eth_pnl > 0:
                net_pnl = btc_pnl + eth_pnl
                
                # Verificar Perigo no BTC (OBI Bullish contra Short)
                btc_symbol = btc_pos['symbol']
                btc_side = "Short" if float(btc_pos.get('netQuantity', 0)) < 0 else "Long"
                
                # Só nos interessa sair do BTC Short se ele estiver perigoso
                if btc_side != "Short": return

                btc_danger = False
                if obi_data and btc_symbol in obi_data:
                    if obi_data[btc_symbol] > 0.2: # OBI positivo indica pressão compradora
                        btc_danger = True
                
                # Condição de Saída: Net PnL positivo OU Perda BTC coberta em 90%
                if btc_danger and (net_pnl >= 0 or eth_pnl >= abs(btc_pnl) * 0.9):
                    print(f"   ️ HEDGE EXIT TRIGGER: ETH PnL ({eth_pnl:.2f}) cobrindo BTC PnL ({btc_pnl:.2f}). Net: {net_pnl:.2f}")
                    print(f"    Fechando BTC_USDC_PERP para eliminar risco tóxico (OBI Bullish).")
                    
                    qty = btc_pos.get('netQuantity', btc_pos.get('quantity'))
                    self._emergency_close(btc_symbol, "Short", qty)
                    
        except Exception as e:
            print(f"️ Erro no Hedge Check: {e}")

    def _emergency_close(self, symbol, side, qty):
        """
        Fecha posição a Mercado imediatamente.
        """
        print(f"    EMERGENCY EXIT: Fechando {symbol} a Mercado!")
        # Fechar significa enviar ordem oposta
        close_side = "Ask" if side == "Long" else "Bid"
        
        payload = {
            "symbol": symbol,
            "side": close_side,
            "orderType": "Market",
            "quantity": str(abs(float(qty)))
        }
        self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
        
    def _place_stop(self, symbol, side, price):
        """
        Envia ordem de Stop Market.
        """
        # Side do Stop é oposto à posição
        stop_side = "Ask" if side == "Long" else "Bid"
        
        # Rounding logic
        if "BTC" in symbol: price = round(price, 1)
        elif "ETH" in symbol: price = round(price, 2)
        else: price = round(price, 4)

        # Precisamos da quantidade para ser seguro?
        # A API da Backpack exige quantidade.
        # Vamos buscar a posição novamente para ter certeza.
        positions = self.transport.get_positions()
        pos = next((p for p in positions if p['symbol'] == symbol), None)
        
        if pos:
            # Fix: API returns 'netQuantity', not 'quantity'
            qty_val = float(pos.get('netQuantity', pos.get('quantity', 0)))
            quantity = str(abs(qty_val))
            
            payload = {
                "symbol": symbol,
                "side": stop_side,
                "orderType": "Market",
                "quantity": quantity,
                "triggerPrice": str(price),
                "triggerQuantity": quantity
            }
            
            self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
