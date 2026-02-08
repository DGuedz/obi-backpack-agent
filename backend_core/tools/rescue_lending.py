import os
import time
import base64
import requests
import sys
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

class BackpackLendingClient:
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

    def get_collateral(self):
        # Tenta endpoint de collateral para ver o que está travado
        url = f"{self.base_url}/api/v1/capital" # O endpoint capital ja mostra o que ta locked/staked
        instruction = "balanceQuery"
        headers = self._headers(instruction)
        try:
            r = requests.get(url, headers=headers)
            return r.json()
        except:
            return {}

    def withdraw_from_lending(self, symbol, quantity):
        # A documentação oficial da Backpack para Lending/Borrowing não está 100% clara em todos os endpoints publicos.
        # Mas geralmente segue o padrão: /api/v1/borrow/withdraw ou /api/v1/lending/withdraw
        # Vamos tentar o endpoint de Transfer ou Withdraw especifico se documentado.
        
        # Como fallback, vamos usar uma instrução genérica de saque se houver, 
        # mas a Backpack pode usar "withdraw" apenas para blockchain.
        
        # Pela doc recente, não há endpoint EXPLICITO de "withdraw from lending" na API publica V1.
        # Isso geralmente significa que deve ser feito via UI ou endpoint não documentado.
        
        # TENTATIVA: Usar endpoint de colateral (se for tratado como colateral)
        print(f"Tentando sacar {quantity} {symbol} do Lending...")
        
        # Como não temos endpoint garantido, vamos apenas logar o saldo travado para confirmação
        return False

def run_rescue():
    print("=== RESGATE DE FUNDOS DO LENDING ===")
    client = BackpackLendingClient(API_KEY, API_SECRET)
    
    print("1. Analisando Saldos...")
    balances = client.get_collateral()
    
    if 'USDC' in balances:
        usdc = balances['USDC']
        print(f"   USDC Status: {usdc}")
        
        # A API retorna: available, locked, staked
        # "staked" ou "locked" geralmente é onde o lending fica
        
        locked = float(usdc.get('locked', 0))
        staked = float(usdc.get('staked', 0))
        
        if locked > 0 or staked > 0:
            print(f"   [!] Detectado {locked + staked} USDC indisponível (Lend/Lock).")
            print("   [AVISO] A API Pública da Backpack V1 atualmente não expõe endpoint de 'Unstake/Withdraw from Earn'.")
            print("   [AÇÃO NECESSÁRIA] Por favor, vá na interface web:")
            print("   1. Aba 'Lend' ou 'Earn'")
            print("   2. Selecione USDC")
            print("   3. Clique em 'Withdraw' para mover para o saldo Spot.")
        else:
            print("   [INFO] Nenhum saldo bloqueado detectado via API. Verifique se já não foi liberado.")
            
    else:
        print("   [INFO] Conta sem registro de USDC.")

if __name__ == "__main__":
    run_rescue()
