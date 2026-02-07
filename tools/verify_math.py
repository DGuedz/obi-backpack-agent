import sys
import os

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backpacktrading/tools
project_root = os.path.dirname(current_dir) # .../backpacktrading
obi_core_path = os.path.join(project_root, 'obiwork_core')
tools_path = os.path.join(obi_core_path, 'tools')

sys.path.append(project_root)
sys.path.append(obi_core_path)
sys.path.append(tools_path)

from airdrop_calculator import OBICalculator

def verify():
    calc = OBICalculator()
    
    # Parâmetros de Teste
    capital = 300.0
    leverage = 10.0
    trades = 20
    fdv = 1.5
    alloc = 20.0
    
    print(f" INICIANDO VERIFICAÇÃO MATEMÁTICA...")
    print(f"   Inputs: Capital=${capital}, Lev={leverage}x, Trades={trades}, FDV=${fdv}B, Alloc={alloc}%")
    
    res = calc.calculate_potential(capital, leverage, trades, fdv, alloc)
    
    # Cálculos Manuais Esperados
    # Daily = 300 * 10 * 20 * 2 = 120,000
    # Total = 120,000 * 45 = 5,400,000
    expected_vol = 5_400_000.0
    
    # Fees = 5,400,000 * 0.0007 = 3,780
    expected_fees = 3_780.0
    
    # Pool = 1.5B * 0.20 = 300M
    # Global = 80B
    # Share = 5.4M / 80B = 0.0000675
    # Value = 300M * 0.0000675 = 20,250
    expected_value = 20_250.0
    
    expected_roi = 20_250.0 / 3_780.0 # ~5.357
    
    print("\n RESULTADOS:")
    print(f"   Volume Total:   Calculado=${res['Total Volume ($)']:,.2f} | Esperado=${expected_vol:,.2f}")
    print(f"   Taxas (Custo):  Calculado=${res['Fees Cost ($)']:,.2f}   | Esperado=${expected_fees:,.2f}")
    print(f"   Valor Airdrop:  Calculado=${res['Est. Airdrop ($)']:,.2f} | Esperado=${expected_value:,.2f}")
    print(f"   ROI Multiplier: Calculado={res['ROI (x)']:.4f}x        | Esperado={expected_roi:.4f}x")
    
    # Asserts
    assert abs(res['Total Volume ($)'] - expected_vol) < 0.1, "Erro no Volume"
    assert abs(res['Fees Cost ($)'] - expected_fees) < 0.1, "Erro nas Taxas"
    assert abs(res['Est. Airdrop ($)'] - expected_value) < 0.1, "Erro no Valor"
    
    print("\n VERIFICAÇÃO CONCLUÍDA: A MATEMÁTICA É PERFEITA.")

if __name__ == "__main__":
    verify()
