import os
import sys
import time
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

class SafeExecutor:
    def __init__(self, symbol):
        # Auth is handled inside BackpackTrade default init or passed
        from backpack_auth import BackpackAuth
        from dotenv import load_dotenv
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.api = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.symbol = symbol
        self.max_loss_usd = 200.0 # TRAVA DE SEGURANÇA AJUSTADA PARA RECUPERAÇÃO ($200)

    def _validate_risk(self, entry_price, size, stop_loss_price):
        """CÁLCULO MATEMÁTICO DE RISCO PRÉ-ENVIO"""
        if not stop_loss_price:
            raise ValueError(" CRÍTICO: Tentativa de ordem SEM Stop Loss abortada!")
        
        # Cálculo da perda estimada
        if size > 0: # Long
            loss = (entry_price - stop_loss_price) * size
        else: # Short
            loss = (stop_loss_price - entry_price) * abs(size)
            
        if loss > self.max_loss_usd:
            raise ValueError(f" RISCO: Perda projetada (${loss:.2f}) excede o limite de ${self.max_loss_usd}!")
        return True

    def execute_atomic_order(self, side, quantity, leverage, sl_pct):
        """
        EXECUÇÃO ATÔMICA REAL: Ordem de Entrada + Stop Loss Trigger no mesmo Payload.
        Usando stopLossTriggerPrice.
        INCLUI VALIDAÇÃO DE 5 CAMADAS (PRE-FLIGHT CHECKLIST).
        """
        print(f"️ [IRONCLAD PROTOCOL] Iniciando execução atômica para {self.symbol}...")
        
        # --- PRE-FLIGHT CHECKLIST INTEGRATION ---
        # "NENHUMA ordem deve ser enviada para a API execute_order sem antes chamar UltimateChecklist.run_full_scan()."
        try:
            from pre_flight_checklist import UltimateChecklist
            checklist = UltimateChecklist(self.symbol)
            # side in checklist is "Buy" or "Sell". param side is "Buy" or "Sell" (from previous usages)
            # But in previous calls it was "Sell" or "Buy".
            # Note: in execute_recovery_batch.py we pass "Sell" or "Buy".
            # The checklist expects "Buy" or "Sell".
            
            is_approved, result = checklist.run_full_scan(side, leverage)
            
            if not is_approved:
                print(f" BLOQUEIO DO SISTEMA (CHECKLIST): {result}")
                sys.exit(1) # Abort per instruction
                
            # Override SL with Calculated Dynamic SL if desired, or validate current SL.
            # User instruction: "Se o retorno for True, utilize o sl_price retornado no dicionário para configurar o Stop Loss Atômico obrigatório."
            
            # The provided SL (sl_pct) was a manual override (1%). 
            # The Checklist calculates ATR based SL.
            # Let's use the safer one (whichever is tighter? or just Checklist's logic?)
            # Instruction says: "utilize o sl_price retornado".
            # So we OVERRIDE the sl_pct based calculation with the Checklist's ATR based price.
            
            sl_price = result['sl_price']
            print(f"    Stop Loss Ajustado pelo Checklist (ATR): {sl_price:.4f}")
            
        except ImportError:
            print("️ Checklist module not found. Proceeding with caution (Legacy Mode).")
            # If we strictly follow orders, we should probably fail. But for safety of current operation flow:
            # Let's assume checklist is mandatory.
            print(" BLOQUEIO: Checklist é obrigatório.")
            sys.exit(1)
        except Exception as e:
            print(f" Erro na validação do Checklist: {e}")
            sys.exit(1)
            
        # 1. Obter Preço Atual (Already fetched inside checklist but fetching again for order placement logic)
        # Or use entry_price from checklist result
        current_price = result['entry_price']

        # 2. Calcular/Validar SL Rígido (Already done by Checklist)
        if side == "Buy":
            side_param = "Bid"
        else: # Sell
            side_param = "Ask"
            
        # 3. Validar Risco (Legacy check, keep it as double check)
        try:
            self._validate_risk(current_price, float(quantity), sl_price)
        except Exception as e:
            print(f" BLOQUEIO DO SISTEMA (RISK): {e}")
            sys.exit(1) # Mata o processo imediatamente

        print(f" Enviando Ordem ATÔMICA {side} | Preço: {current_price} | SL Trigger: {sl_price}")
        
        # 4. Enviar Ordem Unificada (Entrada + Stop no Payload)
        # O método execute_order foi atualizado para aceitar stop_loss
        response = self.api.execute_order(
            symbol=self.symbol,
            side=side_param,
            order_type="Limit",
            quantity=str(quantity),
            price=str(current_price),
            post_only=True, # OBRIGATÓRIO (Maker)
            stop_loss=sl_price # NOVO PARÂMETRO ATÔMICO
        )
        
        if response and 'id' in response:
            print(" ORDEM ATÔMICA ACEITA PELA EXCHANGE.")
            print(f"   🆔 Order ID: {response['id']}")
            # Não precisamos enviar ordem secundária, pois o SL já foi no payload.
            # Mas podemos verificar se foi registrado (opcional).
        else:
            print(" FALHA NA EXECUÇÃO ATÔMICA. Exchange rejeitou a ordem ou o SL.")
            # Se falhou, nada foi aberto. Seguro.

# Exemplo de Uso:
# agent = SafeExecutor("BTC_USDC_PERP")
# agent.execute_atomic_order("Buy", 0.005, 10, 0.02)
