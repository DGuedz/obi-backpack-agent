
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def check_expiry():
    transport = BackpackTransport()
    print(" OBI PREDICTION EXPIRY CHECK")
    
    # Símbolos que apostamos
    my_bets = ["FDVEXTD800M", "FDVPARA1N5B", "FDVEDGEX4B"]
    
    markets = transport.get_prediction_markets()
    if not markets: return

    print("\n DATAS DE RESOLUÇÃO (Quando sai o resultado?):")
    
    found_any = False
    for m in markets:
        title = m.get('title', '')
        expiry = m.get('estimatedEndDate', 'Unknown')
        
        # Formatar data
        try:
            dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            fmt_date = dt.strftime("%d/%m/%Y")
        except:
            fmt_date = expiry

        # Verificar se é um dos nossos
        is_mine = False
        for pm in m.get('predictionMarkets', []):
            for bet in my_bets:
                if bet in pm.get('marketSymbol', ''):
                    is_mine = True
                    break
        
        if is_mine:
            found_any = True
            print(f"\n    {title}")
            print(f"      ️ Data Estimada: {fmt_date}")
            print(f"       Regra: {m.get('description', '')[:100]}...")

    if not found_any:
        print("   ️ Não encontrei os mercados apostados na lista ativa.")

if __name__ == "__main__":
    check_expiry()
