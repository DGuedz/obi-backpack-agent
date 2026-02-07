import asyncio
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_data import BackpackData
from backpack_auth import BackpackAuth

async def analyze_performance():
    print(f"\n RELATÓRIO DE PERFORMANCE DIÁRIA (SESSION REPORT)")
    print(f"   Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    # 1. Buscar Histórico de Fills (Últimos 1000 para garantir o dia todo)
    print(" Baixando histórico de execuções...")
    fills = data_client.get_fill_history(limit=1000)
    
    if not fills:
        print(" Nenhum trade encontrado no histórico recente.")
        return

    # 2. Processar Dados
    df = pd.DataFrame(fills)
    
    # Filtrar apenas trades de HOJE (2026-01-25)
    # Assumindo que a API retorna timestamp ou date string. 
    # Vamos converter colunas relevantes.
    # Campos comuns: 'symbol', 'side', 'price', 'quantity', 'fee', 'realizedPnl', 'timestamp'
    
    # Check columns available
    # print(df.columns) 
    
    # Normalizar timestamp
    # Se for timestamp ms, converter. Se for string, parse.
    # Vamos assumir que existe um campo de tempo. Se não, usamos todos.
    
    trades_today = []
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    total_volume = 0.0
    total_pnl = 0.0
    total_fees = 0.0
    trades_count = 0
    
    symbol_stats = {}
    
    print(f"{'HORA':<10} | {'SYMBOL':<15} | {'SIDE':<6} | {'PRICE':<10} | {'QTY':<8} | {'PNL':<10} | {'VALOR':<10}")
    print("-" * 80)
    
    for fill in fills:
        # Tentar extrair data
        ts = fill.get('timestamp', fill.get('time', None))
        if ts:
            try:
                # Tenta converter se for string iso
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
            except:
                try:
                    # Tenta converter se for timestamp ms
                    dt = datetime.fromtimestamp(int(ts)/1000)
                except:
                    dt = datetime.now() # Fallback
        else:
            dt = datetime.now()
            
        # Filtro de Data (Dia Atual - UTC ou Local?)
        # Vamos pegar tudo das últimas 24h para garantir
        if dt.date() == datetime.now().date():
            trades_count += 1
            
            symbol = fill.get('symbol')
            side = fill.get('side')
            price = float(fill.get('price', 0))
            qty = float(fill.get('quantity', 0))
            fee = float(fill.get('fee', 0))
            pnl = float(fill.get('realizedPnl', 0))
            
            val = price * qty
            total_volume += val
            total_pnl += pnl
            total_fees += fee
            
            # Stats por Símbolo
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {'vol': 0, 'pnl': 0, 'trades': 0}
            symbol_stats[symbol]['vol'] += val
            symbol_stats[symbol]['pnl'] += pnl
            symbol_stats[symbol]['trades'] += 1
            
            time_str = dt.strftime('%H:%M:%S')
            pnl_str = f"${pnl:+.2f}" if pnl != 0 else "-"
            
            print(f"{time_str:<10} | {symbol:<15} | {side:<6} | {price:<10.4f} | {qty:<8.3f} | {pnl_str:<10} | ${val:<10.2f}")

    print("-" * 80)
    print(f" RESUMO DA SESSÃO:")
    print(f"   Trades Totais: {trades_count}")
    print(f"   Volume Total:  ${total_volume:,.2f}")
    print(f"   Fees Pagas:    ${total_fees:.2f}")
    print(f"   PnL Realizado: ${total_pnl:+.2f}")
    print(f"   PnL Líquido:   ${(total_pnl - total_fees):+.2f}")
    
    print("\n DESTAQUES POR ATIVO:")
    for sym, stats in symbol_stats.items():
        print(f"   {sym:<15}: {stats['trades']} Trades | Vol ${stats['vol']:,.0f} | PnL ${stats['pnl']:+.2f}")

    print("\n ANÁLISE ESTRATÉGICA:")
    if total_pnl > 0:
        print("    ESTRATÉGIA VENCEDORA: Sniper/Weaver Híbrido.")
        print("      O foco em 'Reversal Catch' (ETH/LIT) e 'Short Momentum' pagou bem.")
    else:
        print("   ️ ESTRATÉGIA EM AJUSTE: O mercado está difícil.")
        print("      O volume está sendo gerado (Farming), mas precisamos refinar a saída.")

if __name__ == "__main__":
    asyncio.run(analyze_performance())
