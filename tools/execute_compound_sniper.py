import os
import time
import subprocess
import sys

# Protocolo Clone #01: "Sprint Final / Compound Sniper"
# Objetivo: Queimar todo o capital acumulado em entradas únicas e sequenciais.
# Foco: Qualidade > Quantidade. Se errar, para e recalibra.

SYMBOLS = ['BTC_USDC_PERP', 'SOL_USDC_PERP', 'ETH_USDC_PERP', 'SUI_USDC_PERP', 'DOGE_USDC_PERP'] 
# Scanner amplo, mas execução única (Single Asset Focus)

LEVERAGE = 5.0 # Alavancagem equilibrada para Compound
OBI_THRESHOLD = 0.6 # OBI Restaurado (Padrão: 0.6) para Qualidade Máxima

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_sentinel():
    cmd = [
        "python3", 
        f"{project_root}/obiwork_core/tools/volume_farmer.py",
        "--symbols", *SYMBOLS,
        "--leverage", str(LEVERAGE),
        "--mode", "surf", # Surf Mode = Seguir a Tendência
        "--obi", str(OBI_THRESHOLD),
        "--min-entry-interval", "300", 
        "--capital-per-trade", "ALL", # KEY: Usar todo o saldo disponível (Compound)
        "--risk-usd", "15.0", # SL mais largo para não morrer no ruído (depende do saldo, mas vamos fixar alto para permitir ATR)
        "--profit-usd", "100.0", # TP Open (Trailing Stop vai cuidar)
        "--reset-orders",
        "--mandatory-sl",
        "--ironclad", # Mantém a proteção de tendência
        "--compound-mode" # NOVO FLAG: Ativa lógica de Single Asset Focus + Full Margin
    ]
    
    print(f" CLONE #01 SENTINEL: Iniciando Protocolo Sprint Final (Compound)...")
    print(f"   -> Modo: COMPOUND SNIPER (Single Asset + Full Margin)")
    print(f"   -> Ativos Scanner: {SYMBOLS}")
    print(f"   -> Alavancagem: {LEVERAGE}x")
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
