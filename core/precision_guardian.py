import math
import logging

class PrecisionGuardian:
    """
    ️ PRECISION GUARDIAN
    Responsável por garantir que todos os preços e quantidades enviados à API
    estejam em conformidade com os filtros do mercado (tickSize, stepSize).
    """
    def __init__(self, transport):
        self.transport = transport
        self.logger = logging.getLogger("PrecisionGuardian")
        self.filters_cache = {}

    def _get_filters(self, symbol):
        if symbol in self.filters_cache:
            return self.filters_cache[symbol]
        
        # Tentar buscar dados reais da API Markets
        try:
            # Endpoint público para metadata de mercados
            url = "https://api.backpack.exchange/api/v1/markets"
            response = self.transport._send_request("GET", "/api/v1/markets", "") # Instrução vazia para público?
            # Ou requests direto já que é public
            import requests
            resp = requests.get(url)
            
            if resp.status_code == 200:
                markets = resp.json()
                for m in markets:
                    s = m['symbol']
                    filters = m.get('filters', {})
                    
                    # Extrair filtros com fallbacks seguros
                    tick_size = float(filters.get('tickSize', filters.get('priceFilter', {}).get('tickSize', 0.01)))
                    step_size = float(filters.get('stepSize', filters.get('quantityFilter', {}).get('stepSize', 1.0)))
                    min_qty = float(filters.get('minQuantity', filters.get('quantityFilter', {}).get('minQuantity', 0)))
                    min_notional = float(filters.get('minNotional', 0)) # Se existir
                    
                    self.filters_cache[s] = {
                        'tickSize': tick_size, 
                        'stepSize': step_size,
                        'minQuantity': min_qty,
                        'minNotional': min_notional
                    }
                
                # Se achou o símbolo, retorna. Se não, cai no fallback.
                if symbol in self.filters_cache:
                    self.logger.info(f"️ Filtros carregados para {symbol}: {self.filters_cache[symbol]}")
                    return self.filters_cache[symbol]
                    
        except Exception as e:
            self.logger.warning(f"️ Falha ao buscar Markets API: {e}. Usando Heurísticas.")

        # Fallback Heuristics
        tick_size = 0.01
        step_size = 1.0
        
        if "BTC" in symbol:
            tick_size = 0.1
            step_size = 0.001
        elif "ETH" in symbol:
            tick_size = 0.01
            step_size = 0.01
        elif "SOL" in symbol:
            tick_size = 0.01
            step_size = 0.1 # SOL geralmente aceita 0.1 ou 0.01, ser conservador.
        elif "HYPE" in symbol:
            tick_size = 0.001
            step_size = 1.0
        elif "SHIB" in symbol or "BONK" in symbol:
            tick_size = 0.000001
            step_size = 1000.0
        else:
            # Genérico para Alts
            tick_size = 0.0001
            step_size = 1.0
            
        self.filters_cache[symbol] = {'tickSize': tick_size, 'stepSize': step_size}
        return self.filters_cache[symbol]

    def format_price(self, symbol, price):
        """
        Arredonda o preço para o tickSize correto e retorna como string.
        """
        filters = self._get_filters(symbol)
        tick_size = filters['tickSize']
        
        if tick_size < 1:
            decimals = int(round(-math.log10(tick_size), 0))
            fmt_str = f"{{:.{decimals}f}}"
            return fmt_str.format(price)
        else:
            # Tick size >= 1 (ex: 10, 1)
            # Round to nearest tick
            rounded = round(price / tick_size) * tick_size
            return str(int(rounded))

    def format_quantity(self, symbol, quantity):
        """
        Arredonda a quantidade para o stepSize correto e retorna como string.
        """
        filters = self._get_filters(symbol)
        step_size = filters['stepSize']
        
        # Round down to step size (floor) to avoid insufficient balance
        steps = math.floor(quantity / step_size)
        rounded_qty = steps * step_size
        
        if step_size < 1:
            decimals = int(round(-math.log10(step_size), 0))
            fmt_str = f"{{:.{decimals}f}}"
            return fmt_str.format(rounded_qty)
        else:
            return str(int(rounded_qty))
