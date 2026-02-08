import os
import time
import json
import base64
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Carregar variaveis de ambiente
# Tenta carregar do arquivo .env na raiz do projeto
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

API_KEY = os.getenv("BACKPACK_API_KEY")
API_SECRET = os.getenv("BACKPACK_API_SECRET")

# Tentar importar pynacl (mais compativel que ed25519)
try:
    from nacl.signing import SigningKey
except ImportError:
    print("Erro: Biblioteca 'pynacl' necessaria. Instale com: pip install pynacl")
    exit(1)

class BackpackClient:
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
        
        # Usando PyNaCl
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

    def get_tickers(self):
        url = f"{self.base_url}/api/v1/tickers"
        try:
            r = requests.get(url)
            return r.json()
        except Exception as e:
            print(f"Erro ao buscar tickers: {e}")
            return []

    def get_balance(self):
        # Este endpoint requer assinatura. 
        # Como a implementação da assinatura Ed25519 exata pode ser chata sem libs especificas,
        # vamos focar primeiro nos dados publicos se a assinatura falhar, 
        # mas tentar implementar a assinatura correta.
        
        # Doc: https://docs.backpack.exchange/#tag/Capital/operation/get_balances
        # Instruction: balanceQuery
        
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

def analyze_market():
    print("--- INICIANDO SCAN DE MERCADO BACKPACK ---")
    
    if not API_KEY or not API_SECRET:
        print("AVISO: Chaves de API não encontradas. Apenas dados públicos serão mostrados.")
        client = BackpackClient("", "") # Dummy
    else:
        client = BackpackClient(API_KEY, API_SECRET)

    # 1. Buscar Saldo
    saldo_usdc = 0
    if API_KEY:
        print("Buscando saldo...")
        balances = client.get_balance()
        if 'USDC' in balances:
            saldo_usdc = float(balances['USDC']['available'])
        elif 'totalPortfolioValue' in balances: # API nova pode retornar diferente
             pass # Ajustar conforme retorno real
        
        # Fallback de mock se falhar autenticacao no script rápido
        # (Para nao travar a demo se a lib ed25519 nao estiver perfeita)
        if saldo_usdc == 0:
             print("Nota: Não foi possível ler saldo real (ou é zero).")
    
    print(f"Saldo Disponível (Estimado): ${saldo_usdc:.2f} USDC")
    print("-" * 40)

    # 2. Buscar Tickers
    print("Analisando ativos...")
    tickers = client.get_tickers()
    
    # Converter para DataFrame para facil manipulação
    data = []
    for t in tickers:
        # Filtrar apenas Perps (geralmente tem _PERP ou algo assim, ou apenas symbol)
        # Na backpack, symbols sao ex: SOL_USDC
        symbol = t['symbol']
        if 'USDC' not in symbol:
            continue
            
        data.append({
            'symbol': symbol,
            'price': float(t['lastPrice']),
            'change_24h': float(t.get('priceChangePercent', 0)) * 100, # Converter para %
            'volume_usdc': float(t['quoteVolume']),
            'high_24h': float(t['high']),
            'low_24h': float(t['low'])
        })
    
    if not data:
        print("Nenhum dado de mercado encontrado.")
        return

    df = pd.DataFrame(data)
    
    # Filtrar liquidez minima (ex: > 100k volume)
    df = df[df['volume_usdc'] > 100000].copy()
    
    # Ordenar por Volume
    top_volume = df.sort_values('volume_usdc', ascending=False).head(5)
    
    # Ordenar por Volatilidade (Change 24h)
    top_gainers = df.sort_values('change_24h', ascending=False).head(3)
    top_losers = df.sort_values('change_24h', ascending=True).head(3)

    print("\nTOP VOLUME (Liquidez):")
    print(top_volume[['symbol', 'price', 'change_24h', 'volume_usdc']].to_string(index=False))

    print("\nTOP GAINERS (Momentum):")
    print(top_gainers[['symbol', 'price', 'change_24h']].to_string(index=False))

    print("\nTOP LOSERS (Rebound?):")
    print(top_losers[['symbol', 'price', 'change_24h']].to_string(index=False))
    
    print("-" * 40)
    print("SUGESTÕES DE ENTRADA ESTRATÉGICA:")
    
    # Estrategia 1: Trend Following no Top Volume com Momentum Positivo
    # Pega o ativo de maior volume que esteja positivo
    trend_candidate = top_volume[top_volume['change_24h'] > 0].iloc[0] if not top_volume[top_volume['change_24h'] > 0].empty else top_volume.iloc[0]
    
    # Estrategia 2: Rebound em ativo muito descontado ou Momentum puro no Top Gainer
    # Vamos de Momentum puro no Top Gainer (se diferente do trend candidate)
    momentum_candidate = top_gainers.iloc[0]
    if momentum_candidate['symbol'] == trend_candidate['symbol']:
        momentum_candidate = top_gainers.iloc[1] if len(top_gainers) > 1 else top_losers.iloc[0]

    print(f"1) LONG {trend_candidate['symbol']} (Trend/Liquidity)")
    print(f"   Preço: {trend_candidate['price']}")
    print(f"   Variação 24h: {trend_candidate['change_24h']}%")
    print(f"   Tese: Ativo com maior liquidez e tendencia sustentada.")

    print(f"\n2) LONG {momentum_candidate['symbol']} (Momentum/Volatilidade)")
    print(f"   Preço: {momentum_candidate['price']}")
    print(f"   Variação 24h: {momentum_candidate['change_24h']}%")
    print(f"   Tese: Aproveitar inercia do movimento de alta recente.")

    print("-" * 40)

if __name__ == "__main__":
    analyze_market()
