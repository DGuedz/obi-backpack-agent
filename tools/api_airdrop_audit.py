import os
import sys
import asyncio
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def audit_account():
    print("️ INICIANDO AUDITORIA PROFUNDA VIA API BACKPACK...")
    load_dotenv()
    
    transport = BackpackTransport()
    
    all_fills = []
    limit = 100
    offset = 0
    has_more = True
    
    print(" Baixando histórico completo de trades (isso pode demorar)...")
    
    while has_more:
        print(f"   ⏳ Buscando lote {offset} - {offset+limit}...")
        try:
            fills = transport.get_fill_history(limit=limit, offset=offset)
            if not fills or len(fills) == 0:
                has_more = False
                break
            
            all_fills.extend(fills)
            offset += len(fills)
            
            if len(fills) < limit:
                has_more = False
                
        except Exception as e:
            print(f" Erro ao buscar fills: {e}")
            break
            
    print(f"\n Total de Fills Recuperados: {len(all_fills)}")
    
    if not all_fills:
        print("️ Nenhum dado encontrado. Verifique suas chaves API.")
        return

    # Processar dados
    processed_data = []
    for fill in all_fills:
        # Tratamento de timestamp
        ts = fill.get('timestamp', 0)
        if isinstance(ts, str):
            if ts.isdigit():
                ts = int(ts)
            else:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts = dt.timestamp() * 1000
                except:
                    ts = 0
        
        dt_obj = datetime.fromtimestamp(ts / 1000 if ts > 10000000000 else ts, tz=timezone.utc)
        
        price = float(fill.get('price', 0))
        qty = float(fill.get('quantity', 0))
        fee = float(fill.get('fee', 0))
        volume = price * qty
        
        processed_data.append({
            'date': dt_obj,
            'symbol': fill.get('symbol'),
            'side': fill.get('side'),
            'price': price,
            'quantity': qty,
            'volume': volume,
            'fee': fee,
            'isMaker': fill.get('isMaker', False),
            'fee_token': fill.get('feeSymbol', 'USDC')
        })
        
    df = pd.DataFrame(processed_data)
    
    # Cálculos Globais
    total_volume = df['volume'].sum()
    total_fees = df['fee'].sum() # Assumindo tudo em USDC ou convertendo mentalmente se for misto
    
    # Fee Ratio
    fee_ratio = (total_fees / total_volume * 100) if total_volume > 0 else 0
    
    print("\n RESULTADOS DA AUDITORIA API")
    print("=" * 60)
    print(f" Volume Total Auditado: ${total_volume:,.2f}")
    print(f" Taxas Totais Pagas:    ${total_fees:,.2f}")
    print(f" Taxa Média Efetiva:    {fee_ratio:.4f}%")
    
    # Análise S4 Sprint Final (8 Jan 2026 - 21 Jan 2026)
    sprint_start = datetime(2026, 1, 8, tzinfo=timezone.utc)
    sprint_end = datetime(2026, 1, 21, 23, 59, 59, tzinfo=timezone.utc)
    
    df_sprint = df[(df['date'] >= sprint_start) & (df['date'] <= sprint_end)]
    sprint_volume = df_sprint['volume'].sum()
    sprint_fees = df_sprint['fee'].sum()
    
    print("\n ANÁLISE DO SPRINT FINAL (S4 W8-W9)")
    print("=" * 60)
    print(f" Período: {sprint_start.date()} a {sprint_end.date()}")
    print(f" Volume no Sprint:      ${sprint_volume:,.2f} ({sprint_volume/total_volume*100:.1f}% do total)")
    print(f" Taxas no Sprint:       ${sprint_fees:,.2f}")
    
    # Top Symbols
    print("\n TOP 5 ATIVOS POR VOLUME")
    print("=" * 60)
    top_symbols = df.groupby('symbol')['volume'].sum().sort_values(ascending=False).head(5)
    for sym, vol in top_symbols.items():
        print(f"   • {sym:<15}: ${vol:,.2f}")
        
    # Comparação com Estimativa Manual
    print("\n️ COMPARAÇÃO: ESTIMATIVA vs REALIDADE")
    print("=" * 60)
    manual_vol = 1_968_170.60
    diff_vol = total_volume - manual_vol
    
    print(f"Volume Manual:   ${manual_vol:,.2f}")
    print(f"Volume API:      ${total_volume:,.2f}")
    print(f"Diferença:       ${diff_vol:,.2f}")
    
    # Custo por Ponto Real
    # ATUALIZAÇÃO S4 (30/01/2026): 
    # S1: 597
    # S3: 229
    # S4: 2121 (Gold)
    # Total: 2947 Pontos
    total_points = 2947
    real_cost_per_point = total_fees / total_points if total_points > 0 else 0
    
    print("\n MÉTRICAS FINAIS DE AIRDROP (DADOS REAIS)")
    print("=" * 60)
    print(f" Pontos Totais (S1+S3+S4): {total_points}")
    print(f" Custo Real por Ponto:    ${real_cost_per_point:.2f}")
    
    # Valuation Model (Cryo Palmar Logic)
    # 1 Point = 0.567 Tokens
    est_tokens = total_points * 0.567
    
    print("\n PROJEÇÃO DE VALOR (MODELO CRYO PALMAR)")
    print("=" * 60)
    print(f" Tokens Estimados: {est_tokens:,.2f} (Taxa 0.567)")
    print("-" * 60)
    
    fdv_scenarios = {
        '$500M': 0.50,  # Token Price if Supply=1B
        '$1B':   1.00,
        '$2B':   2.00,
        '$5B':   5.00,
        '$10B':  10.00
    }
    
    print(f"{'FDV':<8} | {'Token Price':<12} | {'Valor Total':<15} | {'Lucro Líquido':<15}")
    print("-" * 60)
    
    for label, price in fdv_scenarios.items():
        val = est_tokens * price
        profit = val - total_fees
        print(f"{label:<8} | ${price:<11.2f} | ${val:,.2f}        | ${profit:,.2f}")

if __name__ == "__main__":
    asyncio.run(audit_account())
