import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport

def check_pnl():
    load_dotenv()
    transport = BackpackTransport()
    
    print("\n PNL CHECKER - SUSTENTABILIDADE")
    print("=" * 60)
    
    # 1. Obter Histórico de Fills
    print("⏳ Buscando histórico de execuções...")
    fills = transport.get_fill_history(limit=100)
    
    if not fills:
        print(" Nenhum fill encontrado ou erro na API.")
        return

    # 2. Processar Dados
    df = pd.DataFrame(fills)
    
    if df.empty:
        print(" Sem execuções recentes.")
        return
        
    # Converter timestamp se necessário (assumindo que a API retorna 'executedAt' ou similar)
    # Backpack usa 'timestamp' ou 'executedAt'? Vamos verificar imprimindo colunas se der erro.
    
    # Colunas esperadas: symbol, side, price, quantity, fee, realizedPnl (se houver)
    
    # Filtrar apenas hoje (UTC)
    # df['time'] = pd.to_datetime(df['timestamp'], unit='ms') # Ajustar conforme retorno real
    
    print(f" {len(df)} execuções recuperadas.")
    
    # Se tiver realizedPnl, ótimo. Se não, estimamos.
    if 'realizedPnl' in df.columns:
        df['realizedPnl'] = df['realizedPnl'].astype(float)
        df['fee'] = df['fee'].astype(float)
        
        # Agrupar por Símbolo
        summary = df.groupby('symbol').agg({
            'realizedPnl': 'sum',
            'fee': 'sum',
            'quantity': 'count' # Contagem de fills
        }).rename(columns={'quantity': 'fills'})
        
        summary['Net PnL'] = summary['realizedPnl'] - summary['fee']
        
        print("\n PnL REALIZADO (HOJE):")
        print(summary.to_string())
        
        total_gross = summary['realizedPnl'].sum()
        total_fee = summary['fee'].sum()
        total_net = summary['Net PnL'].sum()
        
        print("-" * 60)
        print(f" GROSS PnL: ${total_gross:.2f}")
        print(f" TOTAL FEES: ${total_fee:.2f}")
        print(f" NET PnL:   ${total_net:.2f}")
        print("=" * 60)
        
        if total_net > 0:
            print(" ESTRATÉGIA LUCRATIVA E SUSTENTÁVEL!")
        else:
            print("️ ATENÇÃO: PREJUÍZO LÍQUIDO (TAXAS?). REVISAR PARÂMETROS.")
            
    else:
        print("️ Campo 'realizedPnl' não encontrado. Mostrando dados brutos recentes:")
        print(df[['symbol', 'side', 'price', 'quantity', 'fee']].head(10).to_string())
        print("\nNota: PnL deve ser calculado manualmente ou via endpoint de posições fechadas.")

if __name__ == "__main__":
    check_pnl()
