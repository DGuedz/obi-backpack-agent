import sys
import os
import time
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.technical_oracle import TechnicalOracle
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

class Compass:
    """
     BÚSSOLA MACRO
    Valida a direção do mercado usando agregação de OBI dos Top Assets.
    """
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data)
        
        self.majors = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "BNB_USDC_PERP"]

    def check_direction(self):
        print("\n VERIFICANDO BÚSSOLA DE MERCADO...")
        print("-" * 50)
        
        total_obi = 0
        count = 0
        
        for symbol in self.majors:
            try:
                depth = self.data.get_orderbook_depth(symbol)
                obi = self.oracle.calculate_obi(depth)
                print(f"   {symbol:<15} | OBI: {obi:+.2f}")
                total_obi += obi
                count += 1
            except Exception as e:
                print(f"   {symbol:<15} | Erro: {e}")
                
        if count == 0: return
        
        avg_obi = total_obi / count
        print("-" * 50)
        
        direction = "NEUTRO"
        if avg_obi > 0.15: direction = "NORTE (BULLISH) 🟢"
        elif avg_obi < -0.15: direction = "SUL (BEARISH) "
        
        print(f" DIREÇÃO MAGNÉTICA: {direction}")
        print(f"   Média OBI Majors: {avg_obi:+.2f}")
        
        if avg_obi < -0.3:
            print("\n CONFIRMAÇÃO: A maré está puxando para baixo. Shorts são favorecidos.")
        elif avg_obi > 0.3:
            print("\n️ ALERTA: A maré virou para cima. Cuidado com Shorts.")
        else:
            print("\n️ ALERTA: Maré confusa/lateral. Reduza a mão.")

if __name__ == "__main__":
    compass = Compass()
    compass.check_direction()
