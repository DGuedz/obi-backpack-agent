import ccxt
import json
import os
from dotenv import load_dotenv
import logging

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UniversalExchange")

class UniversalExchange:
    """
    O Adaptador Universal (The Translator).
    Converte comandos estratégicos do OBI (ex: 'Buy BTC') em chamadas de API específicas
    para qualquer corretora suportada pela CCXT (Binance, Backpack, Bybit, etc).
    """
    
    def __init__(self, exchange_id=None):
        load_dotenv()
        self.config = self._load_config()
        self.exchange_id = exchange_id or self.config.get("active_exchange", "backpack")
        self.exchange = self._initialize_exchange()

    def _load_config(self):
        try:
            with open("config/exchanges.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Arquivo config/exchanges.json não encontrado.")
            return {}

    def _initialize_exchange(self):
        """Inicializa a instância CCXT correta com base no ID."""
        logger.info(f" Conectando ao Exchange: {self.exchange_id.upper()}...")
        
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # Carregar chaves do .env (Padrão: EXCHANGE_API_KEY / EXCHANGE_SECRET)
            api_key = os.getenv(f"{self.exchange_id.upper()}_API_KEY")
            secret = os.getenv(f"{self.exchange_id.upper()}_SECRET")
            
            exchange_params = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
            }
            
            # Adicionar opções extras do config.json
            if self.exchange_id in self.config.get("exchanges", {}):
                options = self.config["exchanges"][self.exchange_id].get("options", {})
                exchange_params.update({'options': options})

            exchange = exchange_class(exchange_params)
            
            # Carregar mercados (simulação de conexão)
            # exchange.load_markets() 
            logger.info(f" Conexão Estabelecida com {self.exchange_id.upper()}")
            return exchange
            
        except AttributeError:
            logger.error(f"Exchange '{self.exchange_id}' não suportada pelo CCXT.")
            return None
        except Exception as e:
            logger.error(f"Erro ao inicializar exchange: {e}")
            return None

    # --- Métodos Unificados (The Common Interface) ---

    def get_price(self, symbol):
        """Retorna o preço atual (Ticker) de forma agnóstica."""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.info(f" {self.exchange_id.upper()} | {symbol}: ${price}")
            return price
        except Exception as e:
            logger.error(f"Erro ao buscar preço de {symbol}: {e}")
            return None

    def get_balance(self, currency="USDC"):
        """Retorna o saldo livre de uma moeda específica."""
        try:
            balance = self.exchange.fetch_balance()
            free = balance.get(currency, {}).get('free', 0.0)
            logger.info(f" Saldo {currency}: {free}")
            return free
        except Exception as e:
            logger.error(f"Erro ao buscar saldo: {e}")
            return 0.0

    def create_order(self, symbol, side, amount, price=None, params={}):
        """
        Executa uma ordem (Market ou Limit) adaptada para a exchange atual.
        """
        try:
            type = 'limit' if price else 'market'
            logger.info(f" Executando Ordem: {side.upper()} {amount} {symbol} @ {price or 'MARKET'}")
            
            order = self.exchange.create_order(symbol, type, side, amount, price, params)
            logger.info(f" Ordem Executada! ID: {order['id']}")
            return order
        except Exception as e:
            logger.error(f" Falha na Execução: {e}")
            return None

# --- Exemplo de Uso (Teste Rápido) ---
if __name__ == "__main__":
    # Simulação: OBI decide operar na Binance
    obi_bot = UniversalExchange(exchange_id="binance")
    
    # OBI verifica preço (sem saber que é Binance por baixo dos panos)
    price = obi_bot.get_price("BTC/USDT")
    
    # OBI verifica saldo
    balance = obi_bot.get_balance("USDT")
