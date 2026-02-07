import os
import sys
import asyncio
import pandas as pd
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.backpack_transport import BackpackTransport

async def analyze_seasonal_losses():
    print("️ INICIANDO RAIO-X SAZONAL DE PERDAS (S1-S4)...")
    load_dotenv()
    
    transport = BackpackTransport()
    all_fills = []
    limit = 100
    offset = 0
    has_more = True
    max_retries = 3
    
    # 1. Coleta de Dados
    print(" Baixando histórico completo...")
    while has_more:
        retries = 0
        while retries < max_retries:
            try:
                fills = transport.get_fill_history(limit=limit, offset=offset)
                if not fills:
                    has_more = False
                    break
                
                all_fills.extend(fills)
                offset += len(fills)
                print(f"   ⏳ Processados {len(all_fills)} trades...", end='\r')
                if len(fills) < limit: has_more = False
                break
            except Exception as e:
                retries += 1
                time.sleep(1)
        if retries == max_retries: break
            
    print(f"\n Total de Trades: {len(all_fills)}")
    if not all_fills: return

    # 2. Processamento
    data = []
    for fill in all_fills:
        ts = fill.get('timestamp', 0)
        if isinstance(ts, str):
            if ts.isdigit(): ts = int(ts)
            else:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    ts = dt.timestamp() * 1000
                except: ts = 0
        
        dt_obj = datetime.fromtimestamp(ts / 1000 if ts > 10000000000 else ts, tz=timezone.utc)
        
        data.append({
            'date': dt_obj,
            'fee': float(fill.get('fee', 0)),
            'price': float(fill.get('price', 0)),
            'qty': float(fill.get('quantity', 0)),
            'side': fill.get('side'),
            'symbol': fill.get('symbol'),
            'volume': float(fill.get('price', 0)) * float(fill.get('quantity', 0))
        })

    df = pd.DataFrame(data)
    
    # 3. Definição das Seasons (Datas Aproximadas Baseadas no User Input)
    # S1: Mar 20, 2025 - Jun 26, 2025
    # S3: Jul 03, 2025 - Sep 10, 2025
    # S4: Nov 20, 2025 - Jan 29, 2026 (Hoje)
    
    seasons = {
        'S1 (Mar-Jun 25)': (datetime(2025, 3, 20, tzinfo=timezone.utc), datetime(2025, 6, 26, 23, 59, 59, tzinfo=timezone.utc)),
        'S2/Gap (Jul-Nov 25)': (datetime(2025, 6, 27, tzinfo=timezone.utc), datetime(2025, 11, 19, 23, 59, 59, tzinfo=timezone.utc)), # Inclui S3 aqui para simplificar ou separar se quiser
        'S3 (Jul-Sep 25)': (datetime(2025, 7, 3, tzinfo=timezone.utc), datetime(2025, 9, 10, 23, 59, 59, tzinfo=timezone.utc)),
        'S4 (Nov 25-Jan 26)': (datetime(2025, 11, 20, tzinfo=timezone.utc), datetime(2026, 2, 1, 23, 59, 59, tzinfo=timezone.utc))
    }
    
    # Nota: S3 está dentro do Gap se não cuidarmos. Vamos priorizar S3 e S4.
    
    print("\n ANÁLISE POR TEMPORADA")
    print("=" * 60)
    
    total_fees_global = 0
    total_vol_global = 0
    
    # Analisar S1
    s1_start, s1_end = seasons['S1 (Mar-Jun 25)']
    df_s1 = df[(df['date'] >= s1_start) & (df['date'] <= s1_end)]
    fees_s1 = df_s1['fee'].sum()
    vol_s1 = df_s1['volume'].sum()
    print(f" SEASON 1 (Mar-Jun 25):")
    print(f"   Trades: {len(df_s1)}")
    print(f"   Volume: ${vol_s1:,.2f}")
    print(f"   Taxas:  ${fees_s1:,.2f}")
    
    # Analisar S3
    s3_start, s3_end = seasons['S3 (Jul-Sep 25)']
    df_s3 = df[(df['date'] >= s3_start) & (df['date'] <= s3_end)]
    fees_s3 = df_s3['fee'].sum()
    vol_s3 = df_s3['volume'].sum()
    print(f" SEASON 3 (Jul-Sep 25):")
    print(f"   Trades: {len(df_s3)}")
    print(f"   Volume: ${vol_s3:,.2f}")
    print(f"   Taxas:  ${fees_s3:,.2f}")
    
    # Analisar S4
    s4_start, s4_end = seasons['S4 (Nov 25-Jan 26)']
    df_s4 = df[(df['date'] >= s4_start) & (df['date'] <= s4_end)]
    fees_s4 = df_s4['fee'].sum()
    vol_s4 = df_s4['volume'].sum()
    print(f" SEASON 4 (Nov 25 - Hoje):")
    print(f"   Trades: {len(df_s4)}")
    print(f"   Volume: ${vol_s4:,.2f}")
    print(f"   Taxas:  ${fees_s4:,.2f}")
    
    # Sprint Final S4 (Jan 2026)
    sprint_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    df_sprint = df[df['date'] >= sprint_start]
    fees_sprint = df_sprint['fee'].sum()
    vol_sprint = df_sprint['volume'].sum()
    
    print(f"\n SPRINT FINAL S4 (JANEIRO 2026):")
    print(f"   Trades: {len(df_sprint)}")
    print(f"   Volume: ${vol_sprint:,.2f}")
    print(f"   Taxas:  ${fees_sprint:,.2f}")
    
    # Estimativa de Perda Líquida (Drawdown)
    # Assumindo Depósito de $1000
    # Saldo Atual ~$90
    # Perda Total = $910
    # Taxas Totais Rastreadas
    total_fees_tracked = df['fee'].sum()
    
    print("\n RAIO-X FINAL DE PERDAS")
    print("=" * 60)
    print(f"Depósito:          $1,000.00")
    print(f"Saldo Atual:       $90.00")
    print(f"Perda Total:       $910.00")
    print("-" * 30)
    print(f"Culpado #1 (Taxas):  ${total_fees_tracked:,.2f} ({(total_fees_tracked/910)*100:.1f}% da perda)")
    print(f"Culpado #2 (Market): ${910 - total_fees_tracked:,.2f} ({( (910-total_fees_tracked)/910 )*100:.1f}% da perda)")
    
    # Onde ocorreu a maior queima?
    max_loss_season = max([('S1', fees_s1), ('S3', fees_s3), ('S4', fees_s4)], key=lambda x: x[1])
    print(f"\n️ FASE MAIS CRÍTICA: {max_loss_season[0]}")
    print(f"   Foi onde você mais gastou taxas (${max_loss_season[1]:.2f}).")

if __name__ == "__main__":
    asyncio.run(analyze_seasonal_losses())
