import os
import sys
import time
import json
import base64
import requests
import math
from dotenv import load_dotenv

# Carregar variaveis de ambiente
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

API_KEY = os.getenv("BACKPACK_API_KEY")
API_SECRET = os.getenv("BACKPACK_API_SECRET")

try:
    from nacl.signing import SigningKey
except ImportError:
    print("Erro: Biblioteca 'pynacl' necessaria.")
    exit(1)

class BackpackStrategyClient:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = base64.b64decode(api_secret)
        self.base_url = "https://api.backpack.exchange"

    def _sign(self, instruction, params, timestamp, window=5000):
        param_str = ""
        if params:
            sorted_keys = sorted(params.keys())
            param_str = "&".join([f"{k}={params[k]}" for k in sorted_keys])
        
        message = f"instruction={instruction}"
        if param_str:
            message += f"&{param_str}"
        message += f"&timestamp={timestamp}&window={window}"
        
        signing_key = SigningKey(self.api_secret)
        signed = signing_key.sign(message.encode('utf-8'))
        return base64.b64encode(signed.signature).decode('utf-8')

    def _headers(self, instruction, params={}):
        timestamp = int(time.time() * 1000)
        window = 5000
        signature = self._sign(instruction, params, timestamp, window)
        return {
            "X-API-Key": self.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json"
        }

    def get_balance(self):
        url = f"{self.base_url}/api/v1/capital"
        instruction = "balanceQuery"
        headers = self._headers(instruction)
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"Erro Balance ({r.status_code}): {r.text}")
                return {}
        except Exception as e:
            print(f"Erro ao buscar saldo: {e}")
            return {}

    def get_ticker(self, symbol):
        url = f"{self.base_url}/api/v1/ticker?symbol={symbol}"
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.json()
            return None
        except:
            return None

    def execute_order(self, symbol, side, quantity):
        url = f"{self.base_url}/api/v1/order"
        instruction = "orderExecute"
        
        params = {
            "symbol": symbol,
            "side": side,
            "orderType": "Market",
            "quantity": str(quantity)
        }
            
        headers = self._headers(instruction, params)
        try:
            print(f" >> ENVIANDO ORDEM: {side} {quantity} {symbol} ...")
            r = requests.post(url, json=params, headers=headers)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"    ERRO ({r.status_code}): {r.text}")
                return None
        except Exception as e:
            print(f"    ERRO EXCECAO: {e}")
            return None

def run_strategy():
    print("=== EXECUTANDO ESTRATÉGIA OBIWORK: 50% MARGEM / 5X ALAVANCAGEM ===")
    
    client = BackpackStrategyClient(API_KEY, API_SECRET)
    
    # 1. Obter Saldo
    print("1. Verificando Saldo...")
    balances = client.get_balance()
    
    # Debug: Mostrar chaves disponiveis
    # print(f"DEBUG: Balances Keys: {balances.keys()}")
    
    usdc_available = 0.0
    if 'USDC' in balances:
        usdc_available = float(balances['USDC']['available'])
    
    print(f"   Saldo USDC Disponível: ${usdc_available:.2f}")
    
    if usdc_available < 1.0:
        print("   [!] Saldo insuficiente para operar (< $1).")
        print("   [DEBUG] Ativando modo SIMULAÇÃO com $13.08 (Saldo visto no print)")
        usdc_available = 13.08

    # 2. Calcular Alocação
    margin_to_use = usdc_available * 0.50
    margin_per_asset = margin_to_use / 2.0
    leverage = 5.0
    notional_per_asset = margin_per_asset * leverage
    
    print(f"2. Alocação Definida:")
    print(f"   Margem Total Usada: ${margin_to_use:.2f} (50%)")
    print(f"   Por Ativo: ${margin_per_asset:.2f} x 5 = ${notional_per_asset:.2f} Notional")

    # 3. Definir Ativos
    targets = ['BTC_USDC_PERP', 'ASTER_USDC_PERP']
    
    for symbol in targets:
        print(f"\n3. Processando {symbol}...")
        ticker = client.get_ticker(symbol)
        if not ticker:
            print(f"   [!] Erro ao obter preço de {symbol}. Pulando.")
            continue
            
        price = float(ticker['lastPrice'])
        print(f"   Preço Atual: {price}")
        
        # Calcular Quantidade
        # Qty = Notional / Price
        raw_qty = notional_per_asset / price
        
        # Arredondamento seguro (step size)
        if 'BTC' in symbol:
            qty = math.floor(raw_qty * 1000) / 1000
        else:
            qty = math.floor(raw_qty * 10) / 10 # 1 casa decimal
            
        print(f"   Quantidade Calculada: {qty} (Notional ~${qty * price:.2f})")
        
        if qty <= 0:
            print("   [!] Quantidade zero (saldo insuficiente para lote mínimo). Pulando.")
            continue
            
        # 4. Executar Ordem
        # ATENÇÃO: Se estiver em modo simulação, não envia ordem real se o saldo real for zero
        # Mas vamos tentar enviar para ver o erro da exchange se for o caso, ou apenas logar se for mock
        
        if usdc_available == 13.08 and balances.get('USDC', {}).get('available', '0') == '0':
             print(f"   [SIMULAÇÃO] Enviaria ordem: BUY {qty} {symbol} @ Market")
        else:
             res = client.execute_order(symbol, "Bid", qty)
             if res:
                 print(f"   [OK] Ordem Executada! ID: {res.get('id', 'N/A')}")
             else:
                 print(f"   [FALHA] Não foi possível executar.")

if __name__ == "__main__":
    run_strategy()
