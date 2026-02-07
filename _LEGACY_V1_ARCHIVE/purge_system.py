import os
import shutil

# LISTA BRANCA: APENAS O NECESSÁRIO PARA O PROTOCOLO OMEGA
WHITELIST = [
    "safe_execution.py",      # O novo executor blindado
    "supreme_sentinel.py",    # O monitor de risco (Renamed from sentinel.py)
    "sentinel.py",            # Mantendo o antigo por precaução se referenciado
    "backpack_data.py",       # Dados
    "backpack_trade.py",      # API Trade Wrapper
    "backpack_auth.py",       # Autenticação
    "backpack_indicators.py", # Indicadores
    "technical_oracle.py",    # OBI e Funding Check
    "purge_system.py",        # Este script
    ".env",                   # Chaves
    "requirements.txt",       # Dependências
    "paxg_sniper.py",         # Active Recovery Agent
    "flash_scalper.py",       # Active Recovery Agent
    "market_scanner_v2.py"    # Scanner used for recovery
]

def purge_useless_files():
    root_dir = os.getcwd()
    trash_dir = os.path.join(root_dir, "_LIXO_TOXICO")
    
    if not os.path.exists(trash_dir):
        os.mkdir(trash_dir)
        
    print(f"️ INICIANDO VARREDURA DE ARQUIVOS INÚTEIS...")
    
    count = 0
    for filename in os.listdir(root_dir):
        if filename.endswith(".py") or filename.endswith(".json"):
            if filename not in WHITELIST:
                src = os.path.join(root_dir, filename)
                dst = os.path.join(trash_dir, filename)
                try:
                    shutil.move(src, dst)
                    print(f"️ REMOVIDO: {filename}")
                    count += 1
                except Exception as e:
                    print(f"Erro ao mover {filename}: {e}")
                    
    print(f"\n LIMPEZA CONCLUÍDA. {count} arquivos movidos para '_LIXO_TOXICO'.")
    print("️ Verifique a pasta e delete-a quando estiver pronto.")

if __name__ == "__main__":
    # AUTO-EXECUTE FOR PROTOCOL COMPLIANCE
    print("️ PROTOCOL OMEGA: AUTO-PURGE INITIATED.")
    purge_useless_files()
