import os
import time
import requests
import base64
import json
from backpack_auth import BackpackAuth

import logging

class BackpackTransport:
    """
     BACKPACK TRANSPORT LAYER
    Handles raw API communication with signing and error handling.
    """
    def __init__(self, auth=None):
        self.logger = logging.getLogger("BackpackTransport")
        self.base_url = "https://api.backpack.exchange"
        if auth:
            self.auth = auth
        else:
            self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        
    def _send_request(self, method, endpoint, instruction, payload=None):
        url = f"{self.base_url}{endpoint}"
        headers = self.auth.get_headers(instruction, payload)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=payload)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=payload)
            else:
                return None
                
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f" API ERROR ({response.status_code}): {response.text}")
                print(f"    API ERROR ({response.status_code}): {response.text}")
                return None
        except Exception as e:
            self.logger.error(f" TRANSPORT ERROR: {e}")
            print(f"    TRANSPORT ERROR: {e}")
            return None

    def get_klines(self, symbol, interval, limit=100):
        seconds_map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800,
            "12h": 43200, "1d": 86400, "3d": 259200, "1w": 604800
        }
        
        seconds = seconds_map.get(interval, 3600)
        end_ts = int(time.time())
        start_ts = end_ts - (limit * seconds)
        
        url = f"{self.base_url}/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}&startTime={start_ts}"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"   ️ API KLINES ERROR: {resp.status_code} - {resp.text}")
                return []
        except Exception as e:
            print(f"   ️ TRANSPORT KLINES EXCEPTION: {e}")
            return []

    def get_positions(self):
        """
        Retorna posições em aberto (Perpétuos).
        Endpoint: GET /api/v1/position
        Instrução: positionQuery
        """
        return self._send_request("GET", "/api/v1/position", "positionQuery")

    def get_account_collateral(self):
        """
        Busca saúde da conta e equity disponível (Unified).
        Endpoint: /api/v1/capital/collateral
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
            params['symbol'] = symbol
            
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

    def get_orderbook_depth(self, symbol, limit=5):
        """
        Retorna o topo do livro de ofertas (Bids e Asks).
        Endpoint: GET /api/v1/depth
        Autenticação: Pública
        """
        endpoint = "/api/v1/depth"
        url = f"{self.base_url}{endpoint}"
        params = {"symbol": symbol}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except:
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
        Endpoint: GET /api/v1/history/orders
        Instrução: orderHistoryQueryAll
        """
        endpoint = "/api/v1/history/orders"
        params = {"limit": str(limit)}
        if symbol:
            params['symbol'] = symbol
            endpoint += f"?symbol={symbol}&limit={limit}"
        else:
            endpoint += f"?limit={limit}"
            
        return self._send_request("GET", endpoint, "orderHistoryQueryAll", params)

    def cancel_open_orders(self, symbol=None):
        """
        Cancela todas as ordens abertas.
        Endpoint: DELETE /api/v1/orders
        Instrução: orderCancelAll
        """
        endpoint = "/api/v1/orders"
        payload = {}
        if symbol:
            payload['symbol'] = symbol
            
        return self._send_request("DELETE", endpoint, "orderCancelAll", payload)
