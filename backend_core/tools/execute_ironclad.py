import os
import time
import subprocess
import sys

# Configurações Ironclad (Sobrevivência)
SYMBOLS = ['BTC_USDC_PERP', 'SOL_USDC_PERP']  # Apenas Liquidez Máxima
LEVERAGE = 3.5 # Baixa Alavancagem
CAPITAL = 40  # Mão Pequena para recuperar confiança
OBI_THRESHOLD = 0.7  # OBI ALTO (Certeza do Ganho - Fluxo Forte)
# O Ironclad Mode já aplica o filtro de Tendência 1m Obrigatório

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_sentinel():
    cmd = [
        "python3", 
        f"{project_root}/obiwork_core/tools/volume_farmer.py",
        "--symbols", *SYMBOLS,
        "--leverage", str(LEVERAGE),
        "--mode", "surf",
        "--obi", str(OBI_THRESHOLD),
        "--min-entry-interval", "300", # 5 minutes cooldown
        "--capital-per-trade", str(CAPITAL),
        "--risk-usd", "2.0", # Stop Loss Financeiro (mas o Técnico vai prevalecer)
        "--profit-usd", "5.0", # Deixa o TP mais solto para pegar a tendência (Trailing Stop cuida)
        "--reset-orders",
        "--mandatory-sl",
        "--ironclad" # ATIVA O PROTOCOLO DE SOBREVIVÊNCIA
    ]
    
    print(f"️ IRONCLAD SENTINEL: Iniciando Protocolo de Sobrevivência...")
    print(f"   -> Modo: IRONCLAD (Trend 1m + OBI + ATR SL)")
    print(f"   -> Ativos: {SYMBOLS}")
    print(f"   -> Comando: {' '.join(cmd)}")
    
    # Loop de Auto-Restart (Anti-Falha)
    while True:
        try:
            process = subprocess.Popen(cmd)
            process.wait()
        except KeyboardInterrupt:
            print("\n Sentinel Interrompido pelo Usuário.")
            break
        except Exception as e:
            print(f"️ Erro no Sentinel: {e}")
        
        print(" Reiniciando em 10s...")
        time.sleep(10)

if __name__ == "__main__":
    run_sentinel()
