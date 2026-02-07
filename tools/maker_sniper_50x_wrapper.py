import sys
import os
import time

# Wrapper para permitir execução parametrizada do maker_sniper
# Pois o original tinha SYMBOL hardcoded

# Adicionar path para importar módulo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools import maker_sniper_50x

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 maker_sniper_50x_wrapper.py <SYMBOL> <SIDE>")
        sys.exit(1)
        
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    # Monkey Patch nas configurações globais do módulo
    maker_sniper_50x.SYMBOL = symbol
    
    # Executar
    maker_sniper_50x.maker_sniper(side)
