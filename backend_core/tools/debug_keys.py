import os
import time
import base64
import requests
import sys
from dotenv import load_dotenv

# Forçar carregamento do .env da raiz
# backend_core/tools/debug_keys.py -> ../../.env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

print(f"Carregando .env de: {env_path}")

API_KEY = os.getenv("BACKPACK_API_KEY")
API_SECRET = os.getenv("BACKPACK_API_SECRET")

try:
    from nacl.signing import SigningKey
except ImportError:
    print("Erro: Biblioteca 'pynacl' necessaria.")
    exit(1)

def debug_keys():
    if not API_KEY:
        print("[ERRO] BACKPACK_API_KEY não encontrada no ambiente.")
        return
    if not API_SECRET:
        print("[ERRO] BACKPACK_API_SECRET não encontrada no ambiente.")
        return

    print(f"API KEY (Prefix): {API_KEY[:10]}...")
    print(f"API SECRET (Prefix): {API_SECRET[:10]}...")
    
    # Testar Autenticação (Balance Query)
    base_url = "https://api.backpack.exchange"
    instruction = "balanceQuery"
    timestamp = int(time.time() * 1000)
    window = 5000
    
    # Assinatura
    params = {}
    param_str = ""
    message = f"instruction={instruction}&timestamp={timestamp}&window={window}"
    
    try:
        secret_decoded = base64.b64decode(API_SECRET)
        signing_key = SigningKey(secret_decoded)
        signed = signing_key.sign(message.encode('utf-8'))
        signature = base64.b64encode(signed.signature).decode('utf-8')
    except Exception as e:
        print(f"[ERRO] Falha ao assinar: {e}")
        return

    headers = {
        "X-API-Key": API_KEY,
        "X-Signature": signature,
        "X-Timestamp": str(timestamp),
        "X-Window": str(window),
        "Content-Type": "application/json"
    }
    
    print("\nEnviando Request para /api/v1/capital...")
    try:
        r = requests.get(f"{base_url}/api/v1/capital", headers=headers)
        print(f"Status Code: {r.status_code}")
        print(f"Response Body: {r.text}")
        
        if r.status_code == 200:
            print("\n[SUCESSO] Chaves válidas e autenticadas!")
            data = r.json()
            if 'USDC' in data:
                print(f"Saldo USDC: {data['USDC']['available']}")
            else:
                print("Saldo USDC não encontrado na resposta.")
        else:
            print("\n[FALHA] Erro de autenticação ou permissão.")
            
    except Exception as e:
        print(f"[ERRO] Falha na requisição HTTP: {e}")

if __name__ == "__main__":
    debug_keys()
