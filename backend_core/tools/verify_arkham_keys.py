import os
import time
import base64
import requests
import sys

# Caminho especifico solicitado
target_env = "/Users/doublegreen/backpacktrading/backpack-arkham-agent/.env"

def load_env_manually(filepath):
    keys = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    keys[key.strip()] = value
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
    return keys

env_vars = load_env_manually(target_env)
API_KEY = env_vars.get("BACKPACK_API_KEY")
API_SECRET = env_vars.get("BACKPACK_API_SECRET")

try:
    from nacl.signing import SigningKey
except ImportError:
    print("Erro: Biblioteca 'pynacl' necessaria.")
    exit(1)

def verify():
    print(f"Verificando chaves de: {target_env}")
    
    if not API_KEY or not API_SECRET:
        print("[ERRO] Chaves não encontradas no arquivo.")
        return

    print(f"API KEY: {API_KEY[:4]}***REDACTED***")
    print(f"API SECRET: {API_SECRET[:4]}***REDACTED***")
    
    # Testar Autenticação (Balance Query)
    base_url = "https://api.backpack.exchange"
    instruction = "balanceQuery"
    timestamp = int(time.time() * 1000)
    window = 5000
    
    message = f"instruction={instruction}&timestamp={timestamp}&window={window}"
    
    try:
        secret_decoded = base64.b64decode(API_SECRET)
        signing_key = SigningKey(secret_decoded)
        signed = signing_key.sign(message.encode('utf-8'))
        signature = base64.b64encode(signed.signature).decode('utf-8')
    except Exception as e:
        print(f"[ERRO] Falha ao assinar (Secret pode estar inválido): {e}")
        return

    headers = {
        "X-API-Key": API_KEY,
        "X-Signature": signature,
        "X-Timestamp": str(timestamp),
        "X-Window": str(window),
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.get(f"{base_url}/api/v1/capital", headers=headers)
        if r.status_code == 200:
            print("\n[SUCESSO] Chaves válidas!")
            data = r.json()
            usdc = data.get('USDC', {}).get('available', '0')
            print(f"SALDO USDC: {usdc}")
            
            # Listar qualquer coisa que tenha saldo
            print("Ativos com saldo:")
            for asset, details in data.items():
                avail = float(details.get('available', 0))
                if avail > 0:
                    print(f" - {asset}: {avail}")
        else:
            print(f"\n[FALHA] HTTP {r.status_code}: {r.text}")
            
    except Exception as e:
        print(f"[ERRO] Falha na requisição: {e}")

if __name__ == "__main__":
    verify()
