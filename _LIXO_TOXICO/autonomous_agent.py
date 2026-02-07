import os
import time
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

class AutonomousGuardian:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.log_file = "autonomous_log.txt"

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry)
        with open(self.log_file, "a") as f:
            f.write(entry + "\n")

    def run_autonomy(self):
        self.log(" MODO AUTÔNOMO INICIADO: O MESTRE SAIU.")
        self.log("️ Protocolo de Segurança Máxima Ativo.")
        
        while True:
            try:
                # 1. Health Check (PnL e Margem)
                self.check_health()
                
                # 2. Monitorar FOGO (Oportunidade AWM detectada na imagem)
                self.monitor_fogo_opportunity()
                
                # 3. Log de Status
                self.log(" Sistema operando. Próximo check em 60s...")
                time.sleep(60)
                
            except Exception as e:
                self.log(f"️ Erro no ciclo autônomo: {e}")
                time.sleep(30)

    def check_health(self):
        positions = self.data.get_positions()
        active = [p for p in positions if float(p['netQuantity']) != 0]
        
        total_pnl = sum([float(p['pnlUnrealized']) for p in active])
        self.log(f" Status: {len(active)} Posições | PnL Total: ${total_pnl:.2f}")
        
        # Emergency Stop se o PnL Total cair muito (Ex: -$20)
        if total_pnl < -20.0:
            self.log(" EMERGÊNCIA: PnL Crítico (-$20). Avaliar fechamento.")
            # self.emergency_close_all() # Desativado por enquanto, apenas loga.

    def monitor_fogo_opportunity(self):
        # Baseado na imagem: FOGO -20% e Funding -0.0359%
        # Isso é um setup de REVERSÃO (Short Squeeze) potencial.
        try:
            ticker = self.data.get_ticker("FOGO_USDC_PERP")
            price = float(ticker['lastPrice'])
            funding = float(ticker.get('fundingRate', 0))
            
            if funding < -0.03: # Funding muito negativo
                self.log(f" FOGO RADAR: Preço {price} | Funding {funding*100:.4f}% (Squeeze Potential)")
                # AWM Sniper ou Farm cuidará disso se entrar nos critérios técnicos
        except:
            pass

if __name__ == "__main__":
    guardian = AutonomousGuardian()
    guardian.run_autonomy()
