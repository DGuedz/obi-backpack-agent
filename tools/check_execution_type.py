import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

async def check_execution_type():
    load_dotenv()
    print("\n️ VERIFICAÇÃO DE EXECUÇÃO (MAKER vs TAKER)")
    
    transport = BackpackTransport()
    
    # Buscar últimos 20 fills
    fills = transport.get_fill_history(limit=20)
    
    if not fills:
        print(" Nenhum fill encontrado.")
        return

    print(f"{'TIME':<20} | {'SYMBOL':<15} | {'SIDE':<5} | {'ROLE':<10} | {'FEE':<10} | {'TYPE'}")
    print("-" * 80)
    
    maker_count = 0
    taker_count = 0
    
    for fill in fills:
        ts = fill.get('timestamp')
        # Tratamento de timestamp (igual ao analyze_history)
        if isinstance(ts, str):
             if ts.isdigit(): ts = int(ts)
             else: ts = 0 # Simplificação
        
        # Formatar Time
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(ts / 1000 if ts > 10000000000 else ts)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = "N/A"
            
        symbol = fill.get('symbol')
        side = fill.get('side')
        is_maker = fill.get('isMaker')
        fee = fill.get('fee')
        
        role = " MAKER" if is_maker else " TAKER"
        type_guess = "Limit (Post)" if is_maker else "Market/Instant"
        
        if is_maker: maker_count += 1
        else: taker_count += 1
        
        print(f"{time_str:<20} | {symbol:<15} | {side:<5} | {role:<10} | {fee:<10} | {type_guess}")

    print("-" * 80)
    print(f"RESUMO: {maker_count} Maker (Limit) vs {taker_count} Taker (Market)")
    
    if taker_count > 0:
        print("\n️ CONCLUSÃO: Ordens TAKER (Mercado) foram detectadas.")
        print("   Isso explica as taxas altas. Entradas ou Saídas via Market pagam ~0.05% ou mais.")
    else:
        print("\n CONCLUSÃO: Apenas ordens MAKER detectadas (Taxa Zero ou Rebate).")

if __name__ == "__main__":
    asyncio.run(check_execution_type())
