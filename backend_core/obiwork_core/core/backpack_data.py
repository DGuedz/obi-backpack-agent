import requests
import json
import time
from backpack_auth import BackpackAuth

class BackpackData:
    def __init__(self, auth: BackpackAuth, base_url="https://api.backpack.exchange"):
        self.auth = auth
        self.base_url = base_url.rstrip('/')

    def get_markets(self):
        """
        Retorna todos os mercados disponíveis.
        Endpoint: GET /api/v1/markets
        """
        endpoint = "/api/v1/markets"
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter mercados: {e}")
            return []

    def get_tickers(self):
        """
        Retorna tickers de todos os mercados (Preço, Volume, Funding).
        Endpoint: GET /api/v1/tickers
        """
        endpoint = "/api/v1/tickers"
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_mark_prices(self):
        """
        Retorna os preços de marcação e Funding Rates de todos os símbolos.
        Endpoint: GET /api/v1/markPrices
        """
        endpoint = "/api/v1/markPrices"
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter mark prices: {e}")
            return []

    def get_ticker(self, symbol):
        """
        Retorna ticker de um símbolo específico.
        Endpoint: GET /api/v1/ticker
        """
        endpoint = "/api/v1/ticker"
        url = f"{self.base_url}{endpoint}"
        params = {'symbol': symbol}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def get_account_collateral(self):
        """
        Busca saúde da conta, margem e equity real (Fonte: Docs)
        Endpoint: GET /api/v1/capital/collateral
        Instrução: collateralQuery
        """
        endpoint = "/api/v1/capital/collateral"
        url = f"{self.base_url}{endpoint}"
        instruction = "collateralQuery"
        
        headers = self.auth.get_headers(instruction=instruction)
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter collateral: {e}")
            return {}

    def get_fill_history(self, limit=100, offset=0):
        """
        Busca histórico de execuções para calcular Volume (Fonte: Docs)
        Endpoint: GET /wapi/v1/history/fills
        Instrução: fillHistoryQueryAll
        """
        endpoint = "/wapi/v1/history/fills"
        url = f"{self.base_url}{endpoint}"
        instruction = "fillHistoryQueryAll"
        
        params = {'limit': str(limit), 'offset': str(offset)}
        headers = self.auth.get_headers(instruction=instruction, params=params)
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter histórico de fills: {e}")
            return []

    def get_depth(self, symbol):
        """
        Retorna o Order Book (Depth).
        Endpoint: GET /api/v1/depth
        """
        endpoint = "/api/v1/depth"
        url = f"{self.base_url}{endpoint}"
        params = {'symbol': symbol}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}

    def get_orderbook_depth(self, symbol):
        """
        Alias para get_depth para compatibilidade com Gatekeeper e Sniper.
        """
        return self.get_depth(symbol)

    def get_klines(self, symbol, interval, start_time=None, end_time=None, limit=1000):
        """
        Retorna velas (Klines/Candles) para um símbolo.
        Endpoint: GET /api/v1/klines
        Params: symbol, interval (1m, 5m, 15m, 1h, 4h, 1d), start, end
        """
        endpoint = "/api/v1/klines"
        url = f"{self.base_url}{endpoint}"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start_time:
            # Explicitly cast to int to avoid 400 error
            params['startTime'] = int(start_time)
        else:
             # Auto-calculate startTime if not provided (Required by API)
             seconds_map = {
                "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
                "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800,
                "12h": 43200, "1d": 86400, "3d": 259200, "1w": 604800
             }
             seconds = seconds_map.get(interval, 3600)
             end_ts = int(time.time())
             start_ts = end_ts - (limit * seconds)
             params['startTime'] = start_ts

        if end_time:
            params['endTime'] = int(end_time)
            
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro Klines: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Exception Klines: {e}")
            return []

    def get_balances(self):
        """
        Retorna o saldo disponível para uso (Available).
        Filtra ativos com saldo zerado.
        Endpoint: GET /api/v1/capital
        Instrução: balanceQuery
        """
        endpoint = "/api/v1/capital"
        url = f"{self.base_url}{endpoint}"
        instruction = "balanceQuery"
        
        # Gerar headers de autenticação
        headers = self.auth.get_headers(instruction=instruction)
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            available_balances = {}
            for asset, details in data.items():
                available = float(details.get('available', 0))
                locked = float(details.get('locked', 0))
                
                if available > 0 or locked > 0:
                    available_balances[asset] = {
                        'available': available,
                        'locked': locked
                    }
            
            # Fallback/Merge with Collateral Data for USDC specifically (Unified Account)
            # Se USDC não estiver em balances ou estiver zerado, tentar buscar do collateral
            if 'USDC' not in available_balances or available_balances['USDC']['available'] == 0:
                try:
                    collat = self.get_account_collateral()
                    net_available = float(collat.get('netEquityAvailable', 0))
                    if net_available > 0:
                        available_balances['USDC'] = {
                            'available': net_available,
                            'locked': float(collat.get('netEquityLocked', 0))
                        }
                except:
                    pass
            
            return available_balances

        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter saldo: {e}")

    def get_positions(self):
        """
        Retorna posições em aberto (Perpétuos).
        Endpoint: GET /api/v1/position
        Instrução: positionQuery
        """
        endpoint = "/api/v1/position"
        url = f"{self.base_url}{endpoint}"
        instruction = "positionQuery"
        
        headers = self.auth.get_headers(instruction=instruction)
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Normalização de resposta para lista
                data = response.json()
                result_list = []
                if isinstance(data, list):
                    result_list = data
                elif isinstance(data, dict):
                    # Se for dict, pode ser um único objeto ou conter uma chave de lista
                    result_list = [data] # Assumir único objeto se não for lista clara
                
                # Normalizar 'netQuantity' para 'quantity' se necessário
                for p in result_list:
                    if 'quantity' not in p and 'netQuantity' in p:
                        p['quantity'] = p['netQuantity']
                    # Adicionar side explicitamente se faltar
                    if 'side' not in p and float(p.get('quantity', 0)) != 0:
                        p['side'] = 'Long' if float(p['quantity']) > 0 else 'Short'
                        
                return result_list
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter posições: {e}")
            return []

    def get_open_orders(self, symbol=None):
        """
        Retorna ordens em aberto.
        Endpoint: GET /api/v1/orders
        Instrução: orderQueryAll
        """
        endpoint = "/api/v1/orders"
        url = f"{self.base_url}{endpoint}"
        instruction = "orderQueryAll"
        
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        headers = self.auth.get_headers(instruction=instruction, params=params)
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter ordens: {e}")
            return []

    def get_market_filters(self, symbol):
        """
        Retorna stepSize e tickSize para um símbolo.
        """
        markets = self.get_markets()
        for m in markets:
            if m.get('symbol') == symbol:
                filters = m.get('filters', {})
                quantity_step = filters.get('quantity', {}).get('stepSize', '1')
                price_tick = filters.get('price', {}).get('tickSize', '0.01')
                return {
                    'stepSize': float(quantity_step),
                    'tickSize': float(price_tick)
                }
        return {'stepSize': 1.0, 'tickSize': 0.01} # Defaults conservadores
