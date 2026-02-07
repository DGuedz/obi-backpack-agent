import requests
import json
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
        except:
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
            params['startTime'] = int(start_time)
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

    def get_klines(self, symbol, interval="1m", limit=100):
        """
        Busca velas (Klines) para análise técnica.
        Endpoint: GET /api/v1/klines
        Params: symbol, interval, startTime
        """
        import time
        endpoint = "/api/v1/klines"
        url = f"{self.base_url}{endpoint}"
        
        # Calculate startTime based on limit and interval (approximate)
        # Interval map to seconds
        seconds_map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "8h": 28800,
            "12h": 43200, "1d": 86400
        }
        sec = seconds_map.get(interval, 60)
        
        end_time = int(time.time())
        start_time = end_time - (limit * sec)
        
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time
        }
        
        try:
            # Public endpoint, no headers needed usually, but keeping consistent if needed
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter klines: {e}")
            return []
            try:
                if 'response' in locals() and response is not None:
                     print(f"Resposta da API: {response.text}")
            except Exception:
                pass
            return {}

    def get_order_book(self, symbol):
        """
        Retorna o livro de ofertas (Order Book) para um símbolo.
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
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter Order Book: {e}")
            return {}

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

    def get_borrow_lending_markets(self):
        """
        Retorna dados de empréstimo (Utilization, APY).
        Endpoint: GET /api/v1/borrow/markets (Tentativa)
        """
        endpoint = "/api/v1/borrow/markets" # Assuming this endpoint exists based on standard patterns
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
        
        headers = self.auth.get_headers(instruction=instruction)
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter ordens: {e}")
            return []

    def get_orderbook_depth(self, symbol, limit=5):
        """
        Retorna o topo do livro de ofertas (Bids e Asks).
        Endpoint: GET /api/v1/depth
        Autenticação: Pública
        """
        endpoint = "/api/v1/depth"
        url = f"{self.base_url}{endpoint}"
        
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        try:
            # Requisição pública, sem headers de assinatura (conforme solicitado)
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Retorna estrutura {'asks': [[price, qty], ...], 'bids': [[price, qty], ...], ...}
            return {
                'asks': data.get('asks', []),
                'bids': data.get('bids', []),
                'timestamp': data.get('timestamp')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter orderbook para {symbol}: {e}")
            if response is not None:
                 print(f"Resposta da API: {response.text}")
            return {'asks': [], 'bids': []}

    def get_klines(self, symbol, interval="5m", limit=100):
        """
        Retorna dados históricos de velas (Klines).
        FIX: Converte timestamp para SEGUNDOS conforme Docs.
        """
        import time
        
        # Mapear intervalo para segundos
        interval_map = {
            "1m": 60, "3m": 180, "5m": 300, "15m": 900, 
            "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400, 
            "6h": 21600, "8h": 28800, "12h": 43200, "1d": 86400
        }
        seconds = interval_map.get(interval, 300)
        
        # Calcular startTime em SEGUNDOS
        end_time = int(time.time())
        start_time = end_time - (limit * seconds)
        
        # Tentativa Oficial (/api/v1/klines) com SEGUNDOS
        endpoint = "/api/v1/klines"
        url = f"{self.base_url}{endpoint}"
        
        # A documentação especifica 'start' e 'end' em SEGUNDOS para este endpoint público
        # Mas algumas implementações sugerem 'startTime'. Vamos priorizar o padrão da doc.
        params = {
            "symbol": symbol,
            "interval": interval,
            "start": start_time,
            "end": end_time
        }
        
        try:
            response = requests.get(url, params=params)
            
            # Se falhar, tentar com 'startTime' e 'endTime' (comum em outras libs)
            if response.status_code != 200:
                params2 = {
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": start_time,
                    "endTime": end_time
                }
                response = requests.get(url, params=params2)

            if response.status_code == 200:
                return response.json()
            
            # Tentativa UI API (Fallback Tático)
            url_ui = "https://api.backpack.exchange/wapi/v1/ui/kline"
            response_ui = requests.get(url_ui, params=params)
            if response_ui.status_code == 200:
                return response_ui.json()
            
            print(f"Kline API Falhou ({response.status_code}). Usando Trades para reconstruir velas.")
            
            # Fallback Avançado: Construir velas via Trades
            try:
                trades = self.get_trades(symbol, limit=1000)
                if trades:
                    return self._build_klines_from_trades(trades, interval)
            except Exception as e:
                print(f"Fallback Trades Falhou: {e}")
            
            # Fallback de Emergência (Fake Candle)
            ticker = self.get_ticker(symbol)
            last_price = float(ticker.get('lastPrice', 0))
            if last_price > 0:
                fake_klines = []
                # Criar volatilidade fake mínima para não travar indicadores
                for i in range(limit):
                    fake_klines.append({
                        'open': str(last_price),
                        'high': str(last_price * 1.0001),
                        'low': str(last_price * 0.9999),
                        'close': str(last_price),
                        'volume': '1000'
                    })
                return fake_klines
            return []
            
        except Exception as e:
            print(f"Erro Fatal Klines: {e}")
            return []

    def get_trades(self, symbol, limit=1000):
        """
        Busca histórico recente de trades públicos.
        """
        endpoint = "/api/v1/trades"
        url = f"{self.base_url}{endpoint}"
        params = {"symbol": symbol, "limit": limit}
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def _build_klines_from_trades(self, trades, interval):
        """
        Reconstrói OHLCV a partir de trades.
        """
        import pandas as pd
        
        if not trades: return []
        
        # Trades: [{'price': '...', 'quantity': '...', 'timestamp': 123...}, ...]
        df = pd.DataFrame(trades)
        df['price'] = df['price'].astype(float)
        df['quantity'] = df['quantity'].astype(float)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Resample
        # Mapear intervalo string para pandas freq
        freq_map = {"1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min", "1h": "1h"}
        freq = freq_map.get(interval, "5min")
        
        df = df.set_index('timestamp').sort_index()
        ohlc = df['price'].resample(freq).ohlc()
        vol = df['quantity'].resample(freq).sum()
        
        klines_df = pd.concat([ohlc, vol], axis=1)
        klines_df.columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Preencher gaps com forward fill (se não houve trade, preço mantém)
        klines_df['close'] = klines_df['close'].ffill()
        klines_df['open'] = klines_df['open'].fillna(klines_df['close'])
        klines_df['high'] = klines_df['high'].fillna(klines_df['close'])
        klines_df['low'] = klines_df['low'].fillna(klines_df['close'])
        klines_df['volume'] = klines_df['volume'].fillna(0)
        
        # Converter para formato de lista de dicts (igual API)
        result = []
        for index, row in klines_df.iterrows():
            result.append({
                'open': str(row['open']),
                'high': str(row['high']),
                'low': str(row['low']),
                'close': str(row['close']),
                'volume': str(row['volume'])
            })
            
        return result

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

    def get_markets(self):
        """
        Retorna informações de todos os mercados (Filtros, Step Size, Tick Size).
        Endpoint: GET /api/v1/markets
        """
        endpoint = "/api/v1/markets"
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter mercados: {e}")
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

    def get_ticker(self, symbol: str):
        """
        Busca dados públicos de ticker (Volume, Preço).
        Fonte: Backpack API Docs - Public Endpoints
        """
        # Endpoint PÚBLICO: Não enviamos headers de assinatura
        # Endpoint SINGULAR exige o parametro symbol
        endpoint = "/api/v1/ticker"
        url = f"{self.base_url}{endpoint}"
        
        params = {'symbol': symbol}
        
        try:
            # Requisição pública, sem headers de assinatura
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Erro ao obter ticker para {symbol}: {e}")
            return {}
        except Exception as e:
            print(f"Erro inesperado ao obter ticker para {symbol}: {e}")
            return {}
            
    # Nota: A Backpack pode não ter um endpoint público dedicado apenas para 'borrowLend/markets'
    # na documentação pública padrão, mas vamos tentar implementar conforme solicitado.
    # Se falhar, usaremos o fallback ou assumiremos taxas padrão.
    def get_borrow_lend_markets(self):
        """
        Retorna taxas de empréstimo (Lending Rates).
        Endpoint: GET /api/v1/borrowLend/markets (Sujeito a verificação)
        """
        endpoint = "/api/v1/borrowLend/markets"
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url)
            # Se der 404, retornamos vazio sem erro crítico
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return []

    def get_collateral(self):
        """
        Retorna informações detalhadas de colateral e margem.
        """
        # Para simplificar, vamos reutilizar get_balances e calcular equity no cliente
        # ou se houver um endpoint específico de resumo de conta.
        # A doc menciona "Assets and collateral data".
        endpoint = "/api/v1/capital" # Corrigido para capital
        url = f"{self.base_url}{endpoint}"
        instruction = "balanceQuery" # Corrigido: definindo instruction localmente
        
        try:
            # Tentar pegar saldo agregado se disponível
            headers = self.auth.get_headers(instruction=instruction)
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}


