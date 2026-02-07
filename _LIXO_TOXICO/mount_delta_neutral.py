import os
from dotenv import load_dotenv
from delta_neutral_manager import DeltaNeutralManager

load_dotenv()

def mount_delta_neutral():
    print(" MONTANDO FAZENDA DELTA NEUTRO")
    print("================================")
    
    # 1. Carregar Chaves
    try:
        with open("DELTANEUTRO", "r") as f:
            lines = f.readlines()
            perp_key = lines[2].strip() 
            perp_secret = lines[7].strip()
    except Exception as e:
        print(f"Erro chaves: {e}")
        return

    manager = DeltaNeutralManager(perp_key=perp_key, perp_secret=perp_secret)
    
    # 2. Definição de Capital (30% de cada carteira)
    # Spot Balance
    bal_spot = manager.data_spot.get_balances()
    usdc_spot = float(bal_spot.get('USDC', {}).get('available', 0))
    alloc_spot = usdc_spot * 0.30
    
    # Perp Balance
    bal_perp = manager.data_perp.get_balances()
    usdc_perp = float(bal_perp.get('USDC', {}).get('available', 0))
    alloc_perp = usdc_perp * 0.30 # Apenas referência, o tamanho é ditado pelo Spot
    
    # O Limite é o menor valor entre os dois para manter 1:1
    # Spot precisa comprar X valor. Perp precisa shortar X valor.
    # Se usarmos 1x alavancagem no perp, precisamos de X de colateral.
    # Logo, allocation = min(alloc_spot, alloc_perp)
    
    allocation = min(alloc_spot, alloc_perp)
    
    if allocation < 10:
        print(f" Alocação muito baixa (${allocation:.2f}). Mínimo $10.")
        return

    print(f"    Capital Total Spot: ${usdc_spot:.2f}")
    print(f"    Capital Total Perp: ${usdc_perp:.2f}")
    print(f"    Alocação da Operação (30%): ${allocation:.2f}")
    print(f"   ️ Ativo Escolhido: SOL (Maior Yield Potencial)")
    
    confirm = input(f"   Deseja executar COMPRA SPOT + VENDA PERP de ${allocation:.2f} em SOL? (y/n): ")
    if confirm.lower() != 'y':
        print("   Cancelado.")
        return

    # 3. Execução
    manager.execute_delta_neutral("SOL", allocation)

if __name__ == "__main__":
    mount_delta_neutral()
