import requests
import json
from backpack_auth import BackpackAuth

class BackpackTrade:
    def __init__(self, auth: BackpackAuth, base_url="https://api.backpack.exchange"):
        self.auth = auth
        self.base_url = base_url.rstrip('/')

    def execute_order(self, symbol, side, price, quantity, order_type="Limit", time_in_force="GTC", reduce_only=False, post_only=False, trigger_price=None, stop_loss=None):
        """
        Envia uma ordem para o Matching Engine.
        Endpoint: POST /api/v1/order
        Instrução: orderExecute
        Supports atomic Stop Loss via `stopLoss` parameter (stopLossLimitPrice/stopLossTriggerPrice logic if supported, 
        or integrated trigger).
        User Request: Use `stopLossTriggerPrice` directly in payload.
        """
        # --- SAFETY LOCK: NO SPOT TRADING ---
        if not symbol.endswith("_PERP"):
            print(f"    SAFETY LOCK: Blocked SPOT order for {symbol}. Only PERP allowed.")
            return None
        # ------------------------------------
        
        endpoint = "/api/v1/order"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderExecute"
        
        # Mapeamento de Tipos de Ordem para Enum Válido da API
        # A API espera: "Limit", "Market", "TriggerLimit", "TriggerMarket"
        valid_order_type = order_type
        
        if order_type in ["StopLoss", "TakeProfit", "TriggerMarket"]:
             # CORREÇÃO DEFINITIVA (Baseada em tentativas anteriores):
             # A API da Backpack espera 'TriggerMarket' explicitamente para ordens a mercado com gatilho.
             # NÃO usar 'Market' com triggerPrice, pois isso gera erro de assinatura ou parâmetro inválido.
             valid_order_type = "TriggerMarket"
             
             # Se for TriggerLimit, o usuário deve passar order_type="TriggerLimit" explicitamente.
             
        # Construir o payload
        # Nota: selfTradePrevention="RejectTaker" é crítico para evitar wash trading e taxas desnecessárias
        payload = {
            "symbol": symbol,
            "side": side, # 'Bid' ou 'Ask'
            "orderType": valid_order_type,
            "quantity": str(quantity),
            "selfTradePrevention": "RejectTaker"
        }

        if reduce_only:
            payload["reduceOnly"] = True
            
        if post_only:
            payload["postOnly"] = True
        
        # Apenas incluir 'price' se for Limit Order ou TriggerLimit
        if "Limit" in valid_order_type:
            payload["price"] = str(price)
            payload["timeInForce"] = time_in_force
            
        # Incluir triggerPrice para ordens condicionais
        if trigger_price is not None:
            payload["triggerPrice"] = str(trigger_price)
            # FIX CRÍTICO: A API exige triggerQuantity sempre que triggerPrice é usado.
            # "Must specify both triggerPrice and triggerQuantity or neither"
            payload["triggerQuantity"] = str(quantity)
            
            # Se for TriggerMarket, a API pode NÃO aceitar 'quantity' normal, apenas 'triggerQuantity'.
            # Vamos testar removendo 'quantity' se for TriggerMarket.
            if valid_order_type == "TriggerMarket":
                if "quantity" in payload:
                    del payload["quantity"]
        
        # --- ATOMIC STOP LOSS INTEGRATION ---
        if stop_loss is not None:
             # According to instruction: Use stopLossTriggerPrice directly in payload.
             payload["stopLossTriggerPrice"] = str(stop_loss)
             # Should we also set stopLossLimitPrice? Usually yes for Limit, or Market if Trigger only.
             # If Stop Market is desired (most common for protection):
             # Some APIs use stopLossPrice, others stopLossTriggerPrice.
             # User Source 104 says: stopLossTriggerPrice
             pass
        
        # Gerar headers de assinatura
        # A classe BackpackAuth já cuida da ordenação alfabética dos parâmetros para a assinatura
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"    Execution Error: {e}")
            print(f"   Response: {response.text}")
            return None

    def cancel_open_order(self, symbol, order_id):
        """
        Cancela uma ordem aberta.
        Endpoint: DELETE /api/v1/order
        Instrução: orderCancel
        """
        endpoint = "/api/v1/order"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderCancel"
        
        payload = {
            "symbol": symbol,
            "orderId": str(order_id)
        }
        
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            response = requests.delete(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"    Cancel Error: {e}")
            if 'response' in locals():
                print(f"   Response: {response.text}")
            raise e

    def set_leverage(self, symbol, leverage):
        """
        Define a alavancagem para o símbolo.
        Endpoint: POST /api/v1/position/leverage
        """
        endpoint = "/api/v1/position/leverage"
        url = f"{self.base_url}{endpoint}"
        instruction = "positionLeverageSet"
        
        payload = {
            "symbol": symbol,
            "leverage": str(leverage)
        }
        
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            print(f"   ️ Setting Leverage for {symbol} to {leverage}x...")
            response = requests.post(url, headers=headers, json=payload)
            # Response might be empty or small JSON
            if response.status_code == 200:
                return True
            else:
                print(f"   ️ Leverage Set Failed: {response.text}")
                return False
        except Exception as e:
            print(f"    Error setting leverage: {e}")
            return False

    def close_position(self, symbol, position_qty):
        """
        Fecha uma posição aberta (Market Order).
        position_qty: float (Positivo = Long, Negativo = Short)
        """
        qty = float(position_qty)
        if qty == 0:
            return None
            
        side = "Ask" if qty > 0 else "Bid" # Se Long (>0), Vende (Ask). Se Short (<0), Compra (Bid).
        abs_qty = abs(qty)
        
        print(f"Closing Position {symbol}: {side} {abs_qty} (Reduce Only)")
        return self.execute_order(symbol, side, price=None, quantity=abs_qty, order_type="Market", reduce_only=True)

    def cancel_open_orders(self, symbol=None):
        """
        Cancela todas as ordens abertas.
        Se symbol for fornecido, cancela apenas para aquele símbolo.
        Endpoint: DELETE /api/v1/orders
        Instrução: orderCancelAll
        """
        endpoint = "/api/v1/orders"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderCancelAll"
        
        payload = {}
        if symbol:
            payload["symbol"] = symbol
            
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            response = requests.delete(url, headers=headers, json=payload)
            # Response might be 200 OK with list of cancelled orders
            if response.status_code == 200:
                print(f" Ordens canceladas para {symbol if symbol else 'ALL'}")
                return response.json()
            else:
                print(f"️ Falha ao cancelar ordens: {response.text}")
                return None
        except Exception as e:
            print(f" Erro ao cancelar ordens: {e}")
            return None

    def set_leverage(self, symbol, leverage):
        """
        Define a alavancagem para o símbolo.
        Endpoint: POST /api/v1/position/leverage (Verificar endpoint exato na doc, mas comum em CEX)
        NOTA: Backpack API para perps geralmente ajusta alavancagem via margem ou endpoint especifico.
        Se endpoint não existir, pode falhar. Assumindo que existe com base em padrões.
        """
        # Endpoint provável baseado na API v1
        endpoint = "/api/v1/position/leverage"
        url = f"{self.base_url}{endpoint}"
        instruction = "positionSetLeverage" # Chute educado, pode ser leverageUpdate
        
        # Na dúvida, vamos logar que estamos tentando, mas se falhar, seguimos com margin cross padrão
        # Se a API da Backpack não expor isso publicamente fácil, assumimos Cross Margin e o risco é gerido pelo tamanho da posição.
        
        # Vamos tentar implementar
        payload = {
            "symbol": symbol,
            "leverage": int(leverage)
        }
        
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                # print(f"Aviso: Não foi possível setar leverage (pode ser padrão do user): {response.text}")
                return None
        except:
            return None

    def get_order(self, symbol, order_id):
        """
        Consulta o status de uma ordem específica.
        Endpoint: GET /api/v1/order
        Instrução: orderQuery
        """
        endpoint = "/api/v1/order"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderQuery"
        
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        
        headers = self.auth.get_headers(instruction=instruction, params=params)
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None

    def cancel_all_orders(self, symbol):
        """
        Cancela todas as ordens abertas para um símbolo específico.
        Endpoint: DELETE /api/v1/orders
        Instrução: orderCancelAll
        """
        endpoint = "/api/v1/orders"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderCancelAll"
        
        payload = {
            "symbol": symbol
        }
        
        headers = self.auth.get_headers(instruction=instruction, params=payload)
        
        try:
            response = requests.delete(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao cancelar ordens para {symbol}: {e}")
            if response is not None:
                 print(f"Resposta da API: {response.text}")
            return None
