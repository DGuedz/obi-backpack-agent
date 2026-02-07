
import os
import sys
import asyncio
import time
import subprocess
from dotenv import load_dotenv

# Path fix for Trae env
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'obiwork_core'))

def run_volume_farmer():
    """
    Executa o Volume Farmer em loop infinito (Auto-Restart).
    Configuração Night Owl (Recalibrado para Recuperação):
    - Symbols: BTC, SOL
    - Leverage: 3.5x
    - TP: 0.5% (Scalp Curto)
    - OBI: 0.8 (Extrema Precisão)
    - Min Interval: 300s (5min)
    """
    
    cmd = [
        "python3", 
        f"{project_root}/obiwork_core/tools/volume_farmer.py",
        "--symbols", "BTC_USDC_PERP", "SOL_USDC_PERP",
        "--leverage", "3.5",
        "--mode", "surf",
        "--obi", "0.8", # Night Owl Extreme Precision
        "--min-entry-interval", "300", # 5 minutes cooldown
        "--capital-per-trade", "40",
        "--risk-usd", "1.4", # Stop 1.0% (estancar sangria)
        "--profit-usd", "0.7", # TP 0.5% (garantir acerto)
        "--reset-orders",
        "--mandatory-sl" # Force SL placement or close position
    ]
    
    while True:
        print("\n NIGHT OWL SENTINEL: Iniciando Volume Farmer...")
        print(f"   -> Comando: {' '.join(cmd)}")
        
        try:
            # Run blocking process
            process = subprocess.Popen(cmd)
            process.wait() # Wait for it to finish (or crash)
            
            exit_code = process.returncode
            print(f"️ Volume Farmer parou (Exit Code: {exit_code}). Reiniciando em 10s...")
            
        except Exception as e:
            print(f" Erro crítico no Sentinel: {e}")
            
        time.sleep(10) # Cool off before restart

if __name__ == "__main__":
    run_volume_farmer()
