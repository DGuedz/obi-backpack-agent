
import os
import time
import requests
import base64
import json
from dotenv import load_dotenv
try:
    from .backpack_auth import BackpackAuth
except ImportError:
    from backpack_auth import BackpackAuth

class BackpackTransport:
    """
     BACKPACK TRANSPORT LAYER
    Handles raw API communication with signing and error handling.
    """
    def __init__(self, api_key=None, api_secret=None):
        self.base_url = "https://api.backpack.exchange"
        # Force reload from env to ensure new keys are picked up
        load_dotenv(override=True)
        key = api_key if api_key else os.getenv('BACKPACK_API_KEY')
        secret = api_secret if api_secret else os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(key, secret)
        self.session = requests.Session()
        
    def _send_request(self, method, endpoint, instruction, payload=None):
        url = f"{self.base_url}{endpoint}"
        
        # Revert: Pass instruction to get_headers explicitly
        headers = self.auth.get_headers(instruction, payload)
        
        if payload is None:
            payload = {}
            
        # FIX: Do NOT add timestamp/window to payload/params.
        # They are already in the headers and the signature.
        # Adding them to query params causes signature mismatch on WAPI endpoints.
        # if payload is not None:
        #    payload['timestamp'] = headers['X-Timestamp']
        #    payload['window'] = headers['X-Window']
        
        try:
            if method == "GET":
                # Important: Pass payload as params so they are actually sent!
                # Remove Content-Type for GET if present?
                if "Content-Type" in headers:
                    del headers["Content-Type"]
                response = self.session.get(url, headers=headers, params=payload)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=payload)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, json=payload)
            else:
                return None
                
            if response.status_code == 200:
                return response.json()
            else:
                print(f"    API ERROR ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"    TRANSPORT ERROR: {e}")
            return None

    def get_klines(self, symbol, interval, limit=100):
        # Calculate startTime if needed (Backpack API requires it often)
        # Interval map to seconds
        seconds_map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800,
            "12h": 43200, "1d": 86400, "3d": 259200, "1w": 604800
        }
        
        seconds = seconds_map.get(interval, 3600)
        end_ts = int(time.time())
        start_ts = end_ts - (limit * seconds)
        
        # Better approach: Pass params dict to requests.get
        url = f"{self.base_url}/api/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'startTime': int(start_ts)
        }
        try:
            resp = self.session.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"   ️ TRANSPORT KLINES EXCEPTION: {e}")
            return []

    def get_funding_rates(self):
        """
        Retorna as taxas de funding atuais para todos os mercados.
        Endpoint (Estimado): GET /api/v1/tickers
        """
        # Nota: API Backpack pode retornar funding no ticker ou endpoint específico.
        # Vamos usar /api/v1/tickers (Plural) se existir, ou iterar.
        # Tentar obter todos os tickers de uma vez.
        url = f"{self.base_url}/api/v1/tickers"
        try:
            resp = self.session.get(url)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"   ️ TRANSPORT TICKERS EXCEPTION: {e}")
            return []

    def get_prediction_markets(self):
        """
        Retorna mercados de predição ativos.
        Endpoint descoberto: GET /api/v1/prediction?resolved=false
        """
        return self._send_request("GET", "/api/v1/prediction", "predictionQuery", {"resolved": "false"})

    def get_max_order_quantity_prediction(self, symbol, side, price):
        """
        Consulta quantidade máxima permitida para predição.
        Endpoint: /api/v1/maxOrderQuantity
        """
        params = {
            "symbol": symbol,
            "side": side,
            "price": str(price)
        }
        return self._send_request("GET", "/api/v1/maxOrderQuantity", "maxOrderQuantityQuery", params)

    def get_all_markets(self):
        """Retorna lista de todos os mercados disponíveis"""
        try:
            url = f"{self.base_url}/api/v1/markets"
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.json()
            return []
        except:
            return []
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"   ️ Funding Fetch Error: {e}")
            return []
            
    def get_open_interest(self):
        """
        Retorna Open Interest (se disponível na API pública).
        Geralmente em /api/v1/markets ou stats.
        """
        # Mock/Simulated ou endpoint real se conhecido.
        # Vamos tentar extrair do 'tickers' se tiver campo 'openInterest' ou 'volume'.
        return []

    def get_positions(self):
        """
        Retorna posições em aberto (Perpétuos).
        Endpoint: GET /api/v1/position
        Instrução: positionQuery
        """
        return self._send_request("GET", "/api/v1/position", "positionQuery")

    def get_assets(self):
        """
        Retorna saldo da carteira SPOT.
        Endpoint: GET /api/v1/assets
        Instrução: assetsQuery
        """
        return self._send_request("GET", "/api/v1/assets", "assetsQuery")

    def get_account_collateral(self):
        """
        Busca saúde da conta.
        Endpoint: /api/v1/capital
        Instruction: balanceQuery
        """
        # Changed from capitalQuery to balanceQuery
        return self._send_request("GET", "/api/v1/capital", "balanceQuery")

    def get_futures_collateral(self):
        """
        Retorna informações detalhadas de colateral e equity de futuros.
        Endpoint: /api/v1/capital/collateral
        Instruction: collateralQuery
        """
        return self._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")

    def get_open_orders(self, symbol=None):
        """
        Retorna ordens em aberto.
        Endpoint: GET /api/v1/orders
        Instrução: orderQueryAll
        """
        endpoint = "/api/v1/orders"
        params = {}
        if symbol:
            endpoint += f"?symbol={symbol}"
            params['symbol'] = symbol # Pass params to signing
            
        return self._send_request("GET", endpoint, "orderQueryAll", params)

    def get_ticker(self, symbol):
        url = f"{self.base_url}/api/v1/ticker?symbol={symbol}"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.json()
            return None
        except:
            return None

    def get_orderbook_depth(self, symbol, limit=100):
        """
        Retorna o livro de ofertas (Bids e Asks).
        Endpoint: GET /api/v1/depth
        Autenticação: Pública
        """
        endpoint = "/api/v1/depth"
        url = f"{self.base_url}{endpoint}"
        params = {"symbol": symbol}
        if limit:
            params['limit'] = str(limit)
            
        try:
            # Use session if available, else requests
            if hasattr(self, 'session'):
                response = self.session.get(url, params=params)
            else:
                response = requests.get(url, params=params)
                
            if response.status_code == 200:
                data = response.json()
                # Ensure Bids are Descending (Best Bid First)
                if data and 'bids' in data and len(data['bids']) > 1:
                    first_bid = float(data['bids'][0][0])
                    last_bid = float(data['bids'][-1][0])
                    if first_bid < last_bid:
                        # print(f"   ️ DEBUG: Reversing Bids for {symbol} (Ascending -> Descending)")
                        data['bids'].reverse()
                        
                # Ensure Asks are Ascending (Best Ask First) - Standard
                # Usually Asks are Low -> High (Best -> Worst)
                # If they were High -> Low, we would reverse.
                # Assuming Asks are correct (Ascending) based on previous debug.
                
                return data
            else:
                print(f"   ️ DEPTH ERROR ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"   ️ DEPTH EXCEPTION: {e}")
            return None

    def cancel_order(self, symbol, order_id):
        """
        Cancela uma ordem específica.
        Endpoint: DELETE /api/v1/order
        Instrução: orderCancel
        """
        payload = {
            "symbol": symbol,
            "orderId": order_id
        }
        return self._send_request("DELETE", "/api/v1/order", "orderCancel", payload)

    def get_order_history(self, limit=100, symbol=None):
        """
        Retorna histórico de ordens.
        Endpoint: GET /wapi/v1/history/orders
        Instrução: orderHistoryQueryAll
        """
        endpoint = "/wapi/v1/history/orders"
        params = {"limit": str(limit)}
        if symbol:
            params['symbol'] = symbol
            endpoint += f"?symbol={symbol}&limit={limit}"
        else:
            endpoint += f"?limit={limit}"
            
        return self._send_request("GET", endpoint, "orderHistoryQueryAll", params)

    def get_fill_history(self, limit=100, symbol=None, offset=0):
        """
        Retorna histórico de execuções (Fills).
        Endpoint: GET /wapi/v1/history/fills
        Instrução: fillHistoryQueryAll
        """
        endpoint = "/wapi/v1/history/fills"
        # Para GET signature na Backpack:
        # 1. Parâmetros devem ir na query string.
        # 2. Parâmetros DEVEM ser passados para get_headers para compor a assinatura.
        
        params = {"limit": str(limit), "offset": str(offset)}
        if symbol:
            params['symbol'] = symbol
        
        # O método _send_request já monta a query string se passarmos params.
        # O importante é que a assinatura (get_headers) receba os mesmos params.
        # No _send_request atual, ele chama get_headers(instruction, payload).
        # Se payload for params, funciona.
        
        return self._send_request("GET", endpoint, "fillHistoryQueryAll", params)

    def get_capital(self):
        """
        Alias for get_account_collateral (for backward compatibility)
        """
        return self.get_account_collateral()

    def transfer_spot_to_futures(self, quantity, symbol="USDC"):
        """
        Transfere fundos de Spot para Futures.
        Endpoint: POST /wapi/v1/capital/deposit
        Instrução: depositCollateral
        """
        # Note: depositCollateral is usually "Spot -> Futures" (Depositing INTO Futures)
        payload = {
            "symbol": symbol,
            "quantity": str(quantity),
            "from": "spot", # Explicitly stating source if API supports/requires it
            "to": "futures"
        }
        
        # Checking correct endpoint/instruction for internal transfer
        # Based on common Backpack API patterns:
        # Deposit to Collateral Account (Futures) from Spot
        return self._send_request("POST", "/wapi/v1/capital/deposit", "depositCollateral", payload)

    def execute_order(self, symbol, order_type, side, quantity, price=None, time_in_force="GTC", trigger_price=None):
        """
        Executa uma ordem na Backpack.
        Endpoint: POST /api/v1/order
        Instrução: orderExecute
        """
        payload = {
            "symbol": symbol,
            "orderType": order_type,
            "side": "Bid" if side == "Buy" or side == "Bid" else "Ask",
            "quantity": str(quantity) if quantity else None
        }
        
        # Se quantity vier como float, tenta formatar para evitar erro de notação científica
        # Mas idealmente o chamador deve passar string formatada pelo PrecisionGuardian
        if isinstance(quantity, float):
             payload["quantity"] = f"{quantity:.8f}".rstrip('0').rstrip('.')
             
        if price:
            payload["price"] = str(price)
            
        if trigger_price:
            payload["triggerPrice"] = str(trigger_price)
            # API requirement: triggerQuantity must be present if triggerPrice is present
            payload["triggerQuantity"] = payload["quantity"]
            
        # Para ordens Market, não enviar price nem timeInForce (geralmente)
        # Mas Backpack suporta IOC/FOK para Market? Default é GTC para Limit.
        if "Limit" in order_type:
            payload["timeInForce"] = time_in_force
            
        # Stop Loss Safety: Always Reduce Only
        if "Stop" in order_type:
             payload["reduceOnly"] = True
             
        # Post Only check? (Not implemented yet in arguments)
        
        return self._send_request("POST", "/api/v1/order", "orderExecute", payload)
