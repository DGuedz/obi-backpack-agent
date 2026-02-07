import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def generate_revenue_report():
    print(" RELATÓRIO CORPORATIVO: DIVERSIFICAÇÃO DE RECEITA", flush=True)
    print("===================================================", flush=True)
    
    try:
        auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        data = BackpackData(auth)
        
        positions = data.get_positions()
    except Exception as e:
        print(f" Erro ao conectar na API: {e}", flush=True)
        return
    active_pos = [p for p in positions if float(p['netQuantity']) != 0]
    
    # Categorias (Unidades de Negócio)
    dept_farm = []
    dept_sniper = []
    dept_hold = []
    
    total_pnl = 0.0
    total_invested = 0.0
    
    print(f"\n ANÁLISE DE PORTFÓLIO ({len(active_pos)} Posições Ativas):")
    print(f"{'DEPARTAMENTO':<15} | {'ATIVO':<10} | {'SIDE':<5} | {'ALAV.':<5} | {'MARGEM ($)':<10} | {'PnL ($)':<10}")
    print("-" * 75)
    
    for p in active_pos:
        symbol = p['symbol'].replace("_USDC_PERP", "")
        side = "Long" if float(p['netQuantity']) > 0 else "Short"
        leverage = int(p.get('leverage', 10)) # Default to 10 if missing
        entry = float(p['entryPrice'])
        qty = float(p['netQuantity'])
        mark = float(data.get_ticker(p['symbol'])['lastPrice'])
        
        margin_used = (abs(qty) * entry) / leverage
        pnl = (mark - entry) * qty
        
        total_pnl += pnl
        total_invested += margin_used
        
        # Classificação Inteligente
        category = "UNKNOWN"
        if leverage <= 5:
            category = " HARVESTER" # Updated Name
            dept_farm.append(pnl)
        elif leverage >= 10 and abs(margin_used) < 150:
            category = "️ SCALP FARM" # Updated Name
            dept_sniper.append(pnl)
        else:
            category = " HOLD/SWING"
            dept_hold.append(pnl)
            
        print(f"{category:<15} | {symbol:<10} | {side:<5} | {leverage}x    | ${margin_used:<9.2f} | ${pnl:+.2f}")

    print("-" * 75)
    
    # Resumo por Departamento
    print("\n RESULTADO POR UNIDADE DE NEGÓCIO (SNOWBALL EFFECT):")
    farm_pnl = sum(dept_farm)
    sniper_pnl = sum(dept_sniper)
    hold_pnl = sum(dept_hold)
    
    print(f"    HARVESTER (Yield):     ${farm_pnl:+.2f}")
    print(f"   ️ SCALP FARM (Volume):   ${sniper_pnl:+.2f}")
    print(f"    HOLD (Estrutural):     ${hold_pnl:+.2f}")
    print(f"   -------------------------------")
    print(f"    LUCRO LÍQUIDO TOTAL:   ${total_pnl:+.2f}")
    
    # Health Check da Empresa
    print(f"\n SAÚDE DA EMPRESA:")
    balances = data.get_balances()
    usdc_avail = float(balances.get('USDC', {}).get('available', 0))
    print(f"    CAIXA LIVRE (OpEx):    ${usdc_avail:.2f}")
    print(f"    CAPITAL ALOCADO:       ${total_invested:.2f}")
    
    if usdc_avail < 100:
        print("   ️ ALERTA: Caixa Baixo. Priorizar estratégias de Liquidez (Farm).")
    elif total_pnl < -10:
        print("   ️ ALERTA: Drawdown detectado. Reduzir exposição em Sniper.")
    else:
        print("    STATUS: Operação Saudável e Diversificada.")

if __name__ == "__main__":
    generate_revenue_report()
