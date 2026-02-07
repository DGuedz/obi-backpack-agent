import time
import sys
import os
import requests
from dotenv import load_dotenv
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from backpack_auth import BackpackAuth

load_dotenv()
auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))

def check_usdc():
    url = "https://api.backpack.exchange/api/v1/capital"
    headers = auth.get_headers("balanceQuery", {})
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if 'USDC' in data:
                avail = float(data['USDC']['available'])
                if avail > 1.0:
                    print(f"\n SUCESSO! Saldo USDC Detectado: ${avail:.2f}")
                    return avail
    except:
        pass
    return 0.0

def monitor():
    print("⏳ Aguardando liberação do Lending (Withdraw)...")
    while True:
        bal = check_usdc()
        if bal > 0:
            break
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(3)

if __name__ == "__main__":
    monitor()
