import os
import sys
import time
import json
import pandas as pd
from dotenv import load_dotenv

# Configurar Caminhos (Path)
# Adiciona diretórios locais para importar módulos core e legacy
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.gatekeeper import Gatekeeper
from core.backpack_transport import BackpackTransport
from core.black_box import BlackBox
from core.learning_engine import LearningEngine

class ConfluenceSniper:
    """
     CONFLUENCE SNIPER (Operação Cirúrgica - Chimera Protocol V3)
    Fusão de Gatekeeper + Sniper Executor + Aprendizado por Reforço.
    Monitora -> Valida -> Grava Contexto -> Executa (Atomicamente).
    """
    def __init__(self, symbol="BTC_USDC_PERP"):
        load_dotenv()
        self.symbol = symbol
        self.transport = BackpackTransport()
        
        # Inicializa Data e Gatekeeper
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.gatekeeper = Gatekeeper(self.data)
        
        # Inicializa Protocolo Chimera
        self.black_box = BlackBox()
        self.learning_engine = LearningEngine()
        
        # Parâmetros de Gestão Rigorosa
        self.RISK_PCT = 0.001   # 0.1% Risco (SL) - HIPER SCALP
        self.TARGET_PCT = 0.05  # 5% Alvo (TP)
        self.RESERVE_PCT = 0.30 # 30% Reserva Intocável
        
        # Estado para Dashboard
        self.status_file = "sniper_status.json"

    def _update_dashboard_status(self, state, data=None):
        """Exporta o estado atual para o DApp (Streamlit)."""
        try:
            status_payload = {
                "timestamp": time.time(),
                "human_time": datetime.now().isoformat(),
                "symbol": self.symbol,
                "state": state, # SCANNING, IN_POSITION, LOCKOUT
                "data": data or {}
            }
            with open(self.status_file, "w") as f:
                json.dump(status_payload, f, indent=4)
        except Exception:
            pass

    def _calculate_dynamic_risk(self, symbol):
        """
        Calcula a volatilidade (ATR) para definir um SL inteligente.
        Retorna (sl_pct, volatility_msg)
        """
        try:
            klines = self.data.get_klines(symbol, "15m", limit=20)
            if not klines:
                return 0.005, "Default (No Klines)" # Default 0.5%
            
            df = pd.DataFrame(klines)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            # Simple ATR approx (High - Low) average
            df['tr'] = df['high'] - df['low']
            atr = df['tr'].mean()
            current_price = df.iloc[-1]['close']
            atr_pct = atr / current_price
            
            # SL = 1.5x ATR (dá espaço para respirar)
            dynamic_sl = atr_pct * 1.5
            
            # Limites de Segurança (Min 0.4% - Max 2%)
            dynamic_sl = max(0.004, min(dynamic_sl, 0.02))
            
            return dynamic_sl, f"Dynamic ({dynamic_sl*100:.2f}% | 1.5x ATR)"
        except Exception as e:
            return 0.005, f"Error ({e}) -> Default 0.5%"

    def run(self):
        print(f"\n CONFLUENCE SNIPER (V3 Chimera) INICIADO - Alvo: {self.symbol}")
        print("   ️  Modo: Atomic Limit (Maker Only) + Reinforcement Learning")
        
        # Tenta evoluir antes de começar
        self.learning_engine.evolve()
        
        print("    Aguardando Alinhamento Perfeito (Macro + Fluxo + Técnica)...")
        
        while True:
            try:
                # 1. Determinar Viés (Flow-First Logic)
                # OBI define a direção. Chart valida.
                approved, reason, context_data = self.gatekeeper.check_confluence(self.symbol, "Buy") # Check Buy first
                obi = context_data.get('obi', 0)
                
                if obi > 0.15: # Fluxo Comprador Forte
                     side = "Buy"
                elif obi < -0.15: # Fluxo Vendedor Forte
                     side = "Sell"
                else:
                     # Fluxo Neutro/Indeciso: Fallback para Técnica (EMA50) mas com cautela
                     klines = self.data.get_klines(self.symbol, "1h", limit=60)
                     if not klines:
                        time.sleep(5)
                        continue
                     df = pd.DataFrame(klines)
                     df['close'] = df['close'].astype(float)
                     ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
                     current_price = df.iloc[-1]['close']
                     side = "Buy" if current_price > ema_50 else "Sell"
                     
                     # Verificar se o OBI contradiz a EMA
                     if side == "Buy" and obi < -0.05:
                         print(f"\r️ Conflito: EMA Buy mas OBI Vendedor ({obi:.2f}). Aguardando...")
                         time.sleep(1)
                         continue
                     if side == "Sell" and obi > 0.05:
                         print(f"\r️ Conflito: EMA Sell mas OBI Comprador ({obi:.2f}). Aguardando...")
                         time.sleep(1)
                         continue

                # 2. Validação Rigorosa (Gatekeeper) + Captura de Contexto
                approved, reason, context_data = self.gatekeeper.check_confluence(self.symbol, side)
                
                # Preço de Entrada: Usar Micro-Precision do Book (Gatekeeper)
                # O Gatekeeper já retorna best_bid/best_ask frescos. Usar isso é mais rápido que Klines.
                if side == "Buy":
                    entry_price = context_data.get('best_bid', current_price)
                else:
                    entry_price = context_data.get('best_ask', current_price)
                
                if not approved:
                    # LOG DE TERMINAL APRIMORADO (RAIO-X)
                    # Exibe o motivo da rejeição e os dados cruciais na mesma linha
                    obi_val = context_data.get('obi', 0)
                    spread_val = context_data.get('spread', 0) * 100
                    funding_val = context_data.get('funding_rate', 0) * 100
                    
                    # Formatação de Cores ANSI para Terminal (opcional, mas ajuda na leitura rápida)
                    # Vermelho para rejeição
                    sys.stdout.write(f"\r [REJEIÇÃO] {reason} | OBI: {obi_val:.2f} | Spread: {spread_val:.3f}% | Funding: {funding_val:.4f}% | Preço Book: {entry_price:.2f}   ")
                    sys.stdout.flush()
                    time.sleep(0.5) # Loop de monitoramento ACELERADO (0.5s) para pegar o book
                    continue
                
                # CALCULAR RISCO DINÂMICO AGORA
                dynamic_sl, risk_msg = self._calculate_dynamic_risk(self.symbol)
                self.RISK_PCT = dynamic_sl # Atualiza o SL da instância
                
                print(f"\n [ALINHAMENTO CONFIRMADO] {self.symbol} | {side} | Preço Book: {entry_price:.2f}")
                print(f"    Raio-X da Aprovação:")
                print(f"      OBI: {context_data.get('obi', 0):.2f} (Fluxo)")
                print(f"      Spread: {context_data.get('spread', 0)*100:.3f}% (Custo)")
                print(f"      Funding: {context_data.get('funding_rate', 0)*100:.4f}% (Taxa)")
                print(f"      ️ Risco Ajustado: {risk_msg}")
                
                # 3. Cálculo de Posição (Gestão de Risco & Reserva)
                capital_check = self._check_capital_safety()
                if not capital_check['safe']:
                    print(f" Abortar: {capital_check['reason']}")
                    time.sleep(60)
                    continue
                
                usable_capital = capital_check['usable_capital']
                
                # Tamanho da Posição (Risk Sizing)
                # Usa o capital disponível (respeitando reserva)
                # Margem de segurança de 5% para taxas/slippage no cálculo
                qty_usdc = usable_capital * 0.95 
                quantity = qty_usdc / entry_price # Usa preço exato do book
                
                # Ajuste de precisão (BTC requer 3 casas decimais para quantity?)
                # Verificar regras do ativo. BTC geralmente é 0.001. SOL é 0.1 ou 1.
                if "BTC" in self.symbol:
                     # A API pode exigir quantity como string
                     quantity = round(quantity, 3)
                elif "SOL" in self.symbol:
                     quantity = round(quantity, 1)
                elif "ETH" in self.symbol:
                     quantity = round(quantity, 2)
                else:
                     quantity = round(quantity, 1)
                
                # Formatação explícita para string para evitar problemas de float no JSON
                quantity_str = str(quantity)
                
                if quantity <= 0:
                    print(" Quantidade Zero calculada (Capital insuficiente para lote mínimo).")
                    time.sleep(10)
                    continue
                
                # 4. Execução Atômica (Entrada + SL + TP)
                # Usa entry_price (do book) para posicionar Maker na cabeça da fila
                order_id = self._execute_atomic_sniper(side, entry_price, quantity)
                
                if order_id:
                    self._update_dashboard_status("IN_POSITION", {"order_id": order_id, "entry_price": current_price, "qty": quantity})
                    
                    # 5. Black Box: Gravar o Contexto do Crime (Snapshot)
                    self.black_box.record_entry_context(order_id, self.symbol, side, context_data)
                    
                    # 6. Monitoramento de Breakeven (Zero Loss Mode)
                    print(" Monitorando para mover SL para Breakeven (Zero Loss)...")
                    self._monitor_for_breakeven(order_id, side, current_price)
                    
                    # 7. Lockout e Encerramento (Modo Single Shot)
                    print(" Operação de Teste Concluída. Encerrando para Análise.")
                    self._update_dashboard_status("COMPLETED", {"reason": "Single Shot Test Finished"})
                    
                    # Tenta evoluir após o trade (embora o resultado só venha depois, a evolução olha o passado)
                    self.learning_engine.evolve()
                    
                    sys.exit(0) # Encerra o script após 1 trade
                
            except KeyboardInterrupt:
                print("\n Sniper Parado pelo Usuário.")
                break
            except Exception as e:
                print(f"\n️ Erro no Loop Principal: {e}")
                time.sleep(5)

    def _monitor_for_breakeven(self, order_id, side, entry_price):
        """
        Monitora o preço em tempo real.
        Se Lucro > 0.2%, move SL para Entrada + 0.1% (Cobre Taxas Taker).
        Matemática: 0.1% Profit - 0.085% Fee = +0.015% Net (Zero Loss).
        """
        # Taxa Taker estimada (pior caso para o Stop)
        TAKER_FEE = 0.00085 
        # Buffer de Lucro Mínimo para garantir Zero Loss
        REQUIRED_NET_PROFIT = 0.00015 # 0.015%
        
        # Onde o SL deve ficar para pagar as contas?
        # Breakeven Real = Entrada * (1 + Taxa Taker + Lucro Minimo)
        if side == "Buy":
            breakeven_sl_price = entry_price * (1 + TAKER_FEE + REQUIRED_NET_PROFIT)
            # Gatilho: Só movemos quando o preço estiver um pouco acima disso para não ser violinado
            trigger_price = entry_price * (1 + 0.002) # 0.2% de alta
        else:
            breakeven_sl_price = entry_price * (1 - TAKER_FEE - REQUIRED_NET_PROFIT)
            trigger_price = entry_price * (1 - 0.002) # 0.2% de queda
            
        print(f"   ️ PLANO ZERO LOSS:")
        print(f"      Entrada: {entry_price}")
        print(f"      Alvo Gatilho: {trigger_price:.2f} (0.2%)")
        print(f"      Novo SL (Meta): {breakeven_sl_price:.2f} (Garante Taxas)")
        
        start_time = time.time()
        # Monitora por até 1 hora ou até sair
        while (time.time() - start_time) < 3600:
            try:
                # Check current price
                ticker = self.data.get_ticker(self.symbol)
                if not ticker: continue
                current_price = float(ticker['lastPrice'])
                
                # Check if trigger hit
                move_sl = False
                if side == "Buy" and current_price >= trigger_price:
                    move_sl = True
                elif side == "Sell" and current_price <= trigger_price:
                    move_sl = True
                    
                if move_sl:
                    print(f"    GATILHO ATIVADO! Movendo SL para Zero Loss...")
                    # Cancelar SL antigo e criar novo?
                    # A Backpack permite editar ordem?
                    # Melhor abordagem: Cancelar ordem de Stop antiga e criar nova Stop Market
                    
                    # 1. Achar a ordem de Stop atual
                    open_orders = self.data.get_open_orders(self.symbol)
                    stop_order = None
                    for o in open_orders:
                        if o.get('orderType') in ['StopLimit', 'StopMarket'] and o.get('triggerPrice'):
                             # Verificar se é o nosso stop (pelo lado oposto)
                             stop_side = "Ask" if side == "Buy" else "Bid"
                             if o.get('side') == stop_side:
                                 stop_order = o
                                 break
                    
                    if stop_order:
                        # Cancelar Stop Antigo
                        self.transport._send_request("DELETE", "/api/v1/order", "orderCancel", 
                                                   {'symbol': self.symbol, 'orderId': stop_order['id']})
                        print("      Stop Antigo Cancelado.")
                        
                    # Criar Novo Stop (Breakeven)
                    stop_side = "Ask" if side == "Buy" else "Bid"
                    sl_payload = {
                        "symbol": self.symbol,
                        "side": stop_side,
                        "orderType": "StopMarket",
                        "triggerPrice": f"{breakeven_sl_price:.2f}",
                        "quantity": str(self.data.get_positions()[0]['quantity']) # Pega quantidade atual da posição
                    }
                    # Ajuste defensivo de quantidade: Pegar da posição real
                    # Se falhar em pegar posição, usa logica do order_id original se salvo?
                    # Vamos confiar no get_positions por enquanto
                    
                    res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", sl_payload)
                    if res:
                         print(f"       NOVO SL (ZERO LOSS) DEFINIDO: {breakeven_sl_price:.2f}")
                    
                    return # Sai do monitoramento, missão cumprida
                
                time.sleep(2)
                
            except Exception as e:
                print(f"   ️ Erro no Monitor Breakeven: {e}")
                time.sleep(5)

    def _check_capital_safety(self):
        """
        Verifica se há capital disponível respeitando a reserva de 30%.
        Retorna dicionário com status e capital usável.
        """
        try:
            collateral = self.transport.get_account_collateral()
            if not collateral:
                return {'safe': False, 'reason': "Falha ao obter Colateral"}
            
            # Tentar extrair Equity (Saldo Total) e Available (Disponível para Trade)
            # A estrutura exata pode variar, implementando busca defensiva (netEquity é o padrão atual)
            total_equity = float(collateral.get('netEquity', collateral.get('equity', collateral.get('balance', 0))))
            available_balance = float(collateral.get('netEquityAvailable', collateral.get('availableToTrade', collateral.get('availableBalance', 0))))
            
            if total_equity <= 0:
                 return {'safe': False, 'reason': "Equity Zero ou Falha na API (netEquity not found)"}

            # Cálculo da Reserva Intocável
            reserve_amount = total_equity * self.RESERVE_PCT
            
            # Capital Máximo Permitido para Uso (70% do Total)
            max_allowed_usage = total_equity * (1 - self.RESERVE_PCT)
            
            # Capital já em uso (Equity - Available)
            used_margin = total_equity - available_balance
            
            # Capital Livre Real (respeitando o teto de 70%)
            # Se eu já usei 50% do capital, só tenho mais 20% livre, mesmo que available mostre 50%.
            usable_capital = max_allowed_usage - used_margin
            
            if usable_capital < 10: # Mínimo $10 para operar
                return {'safe': False, 'reason': f"Reserva Atingida. Livre Real: ${usable_capital:.2f} (Reserva: ${reserve_amount:.2f})"}
                
            print(f"    Capital Check: Equity ${total_equity:.2f} | Reserva ${reserve_amount:.2f} | Usável ${usable_capital:.2f}")
            return {'safe': True, 'usable_capital': usable_capital}
            
        except Exception as e:
            return {'safe': False, 'reason': f"Erro no Check de Capital: {e}"}

    def _execute_atomic_sniper(self, side, price, quantity):
        """
        Envia ordem LIMIT POST ONLY com SL e TP atômicos.
        Se rejeitada (PostOnly Triggered) ou não preenchida, inicia Chase Logic.
        """
        print(f" EXECUTANDO ORDEM ATÔMICA: {side} {quantity} @ {price}")
        
        # Tentativas de Chase (Perseguição Maker)
        MAX_CHASE_ATTEMPTS = 5
        chase_count = 0
        
        while chase_count < MAX_CHASE_ATTEMPTS:
            # Recalcular Preços de Gatilho para a nova tentativa
            if side == "Buy":
                # Tentar pegar o Best Bid atualizado se for Chase
                if chase_count > 0:
                    depth = self.data.get_orderbook_depth(self.symbol)
                    if depth and depth.get('bids'):
                        best_bid = float(depth['bids'][-1][0])
                        # Se meu preço original ficou pra trás, ajusta para Best Bid
                        # Se Best Bid > preço original, subir para Best Bid (Chase)
                        # Mas não pagar Taker! PostOnly garante isso.
                        price = max(price, best_bid)
                
                sl_price = price * (1 - self.RISK_PCT)
                tp_price = price * (1 + self.TARGET_PCT)
                order_side = "Bid"
            else:
                if chase_count > 0:
                    depth = self.data.get_orderbook_depth(self.symbol)
                    if depth and depth.get('asks'):
                        best_ask = float(depth['asks'][0][0])
                        # Se Best Ask < preço original, descer para Best Ask (Chase)
                        price = min(price, best_ask)

                sl_price = price * (1 + self.RISK_PCT)
                tp_price = price * (1 - self.TARGET_PCT)
                order_side = "Ask"
                
            # Formatação
            price_str = f"{price:.2f}" 
            sl_str = f"{sl_price:.2f}"
            tp_str = f"{tp_price:.2f}"
            # qty_str removido daqui pois já temos quantity_str calculado fora do loop de chase
            # Mas se a quantidade mudar? Não muda no chase.
            
            payload = {
                "symbol": self.symbol,
                "side": order_side,
                "orderType": "Limit",
                "quantity": str(quantity), # Garantir que usa a quantidade passada para a função
                "price": price_str,
                "postOnly": True, 
                "selfTradePrevention": "RejectTaker",
                "stopLossTriggerPrice": sl_str,
                "takeProfitTriggerPrice": tp_str
            }
            
            # Envio
            res = self.transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res and 'id' in res:
                print(f" ORDEM ENVIADA! ID: {res['id']} @ {price_str}")
                # Verificar se foi preenchida ou ficou no book?
                # Se for PostOnly e retornou ID, ela entrou no book.
                # Se fosse rejeitada por cruzar spread, daria erro na API.
                return res['id']
            
            # Se falhou, verificar se foi rejeição PostOnly
            # A API da Backpack retorna erro se PostOnly cruzar.
            # Aqui estamos assumindo que _send_request retornou None em caso de erro.
            # Se erro for "PostOnly would take", precisamos ajustar o preço.
            
            print(f"️ Tentativa {chase_count+1} falhou ou rejeitada. Ajustando preço (Chase)...")
            chase_count += 1
            time.sleep(0.5) # Breve pausa antes de tentar novamente (Acelerado para 0.5s)
            
            # Atualizar preço para a próxima iteração do loop
            # O loop já recalcula baseado no book no início
            
        print(" FALHA FINAL NA EXECUÇÃO APÓS CHASE.")
        return None

if __name__ == "__main__":
    # Permite passar simbolo como argumento: python confluence_sniper.py SOL_USDC_PERP
    target = "BTC_USDC_PERP"
    if len(sys.argv) > 1:
        target = sys.argv[1]
        
    bot = ConfluenceSniper(target)
    bot.run()