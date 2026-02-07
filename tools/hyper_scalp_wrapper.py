import sys
import os

# Wrapper para Hyper Scalp Taker Parametrizado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools import hyper_scalp_50x

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 hyper_scalp_wrapper.py <SYMBOL> <SIDE>")
        sys.exit(1)
        
    symbol = sys.argv[1]
    side = sys.argv[2]
    
    # Monkey Patch Global
    hyper_scalp_50x.TARGET_SYMBOL = symbol
    
    # Executar
    hyper_scalp_50x.hyper_scalp_execute(side)
