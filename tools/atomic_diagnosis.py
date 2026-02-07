
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle
from vsc_utils import VSCParser

# Configurar Logging (Console Only para Diagnóstico)
logging.basicConfig(level=logging.WARNING)

class AtomicDiagnostician:
    def __init__(self):
        load_dotenv()
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        self.oracle = TechnicalOracle(self.data_client)
        
    async def diagnose_targets(self):
        print("\n️  DIAGNÓSTICO DE POTÊNCIA ATÔMICA (FONTE DA VERDADE) ️\n")
        print("SYMBOL,SCORE,DIRECTION,OBI,VOL_RISK,ACTION")
        print("-" * 60)
        
        try:
            # Carregar Targets via VSC
            raw_targets = VSCParser.read_file("tools/loop_targets.vsc")
            targets = [r[0] for r in raw_targets if r]
            
            # Loop de Diagnóstico
            for symbol in targets:
                compass = await asyncio.to_thread(self.oracle.get_market_compass, symbol)
                
                score = compass.get('score', 0)
                direction = compass.get('direction', 'NEUTRAL')
                obi = compass.get('obi', 0.0)
                vol_risk = compass.get('volatility_risk', 'LOW')
                
                # Recomendação Simples
                action = "WAIT"
                if score >= 80: action = f"STRONG_{direction}"
                elif score >= 60: action = f"WEAK_{direction}"
                elif score <= 20: action = "AVOID_TOXIC"
                
                # Format VSC Output
                print(f"{symbol},{score},{direction},{obi:.2f},{vol_risk},{action}")
                
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    diag = AtomicDiagnostician()
    asyncio.run(diag.diagnose_targets())
