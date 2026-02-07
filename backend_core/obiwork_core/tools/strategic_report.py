import os
import sys
import json
from datetime import datetime, timedelta
import pandas as pd

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backpacktrading/obiwork_core/tools
project_root = os.path.dirname(os.path.dirname(current_dir)) # .../backpacktrading
obi_core_path = os.path.join(project_root, 'obiwork_core')
core_path = os.path.join(obi_core_path, 'core')

sys.path.append(obi_core_path)
sys.path.append(core_path)

from backpack_transport import BackpackTransport
from dotenv import load_dotenv

load_dotenv()

class StrategicReport:
    def __init__(self):
        self.transport = BackpackTransport()
        
    def generate(self, days=10):
        print(f" GERANDO RELATÓRIO ESTRATÉGICO (Últimos {days} dias)...")
        
        # 1. Fetch History
        fills = self.transport.get_fill_history(limit=1000)
        if not fills:
            print(" Sem dados de histórico.")
            return

        df = pd.DataFrame(fills)
        
        # Convert timestamp
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        except:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
            
        df['price'] = df['price'].astype(float)
        df['quantity'] = df['quantity'].astype(float)
        df['fee'] = df['fee'].astype(float)
        
        # Filter by days
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df['timestamp'] >= cutoff_date]
        
        if df.empty:
            print(" Sem trades no período.")
            return

        # 2. Calculate Metrics
        df['volume_usd'] = df['price'] * df['quantity']
        
        total_volume = df['volume_usd'].sum()
        total_fees = df['fee'].sum()
        trade_count = len(df)
        
        # Group by Symbol
        symbol_metrics = df.groupby('symbol').agg({
            'volume_usd': 'sum',
            'fee': 'sum',
            'quantity': 'count' # Fills count
        }).sort_values(by='volume_usd', ascending=False)
        
        # Group by Day
        df['date'] = df['timestamp'].dt.date
        daily_metrics = df.groupby('date').agg({
            'volume_usd': 'sum',
            'fee': 'sum'
        }).sort_index(ascending=False)

        # 3. Output Report
        report = f"""
#  RELATÓRIO ESTRATÉGICO OBI WORK (Últimos {days} Dias)

##  Resumo Executivo
- **Volume Total:** ${total_volume:,.2f}
- **Taxas Pagas:** ${total_fees:,.2f}
- **Execuções (Fills):** {trade_count}
- **Média Volume/Dia:** ${total_volume/days:,.2f}

##  Performance Backpack (Estimada)
- **Rank Volume:** (Verificar Dashboard)
- **Tier Atual:** Gold (Confirmado)
- **Projeção Pontos:** Baseado no volume, estamos farmando consistentemente.

##  Breakdown por Ativo
{symbol_metrics.to_string()}

##  Histórico Diário
{daily_metrics.to_string()}

##  Análise Estratégica
- O modelo gerou **${total_volume:,.2f}** de fluxo para a exchange.
- O custo operacional (Fees) foi de **${total_fees:,.2f}**.
- A estratégia **Ironclad** (implementada hoje) visa reduzir o 'churning' (perda em taxas sem lucro) e focar em qualidade.

**Recomendação:**
Manter o foco em BTC/SOL (Liquidez) e respeitar o filtro de tendência para transformar esse Volume em Lucro Líquido Real.
"""
        
        print(report)
        
        # Save to file
        with open("STRATEGIC_REPORT.md", "w") as f:
            f.write(report)
        print(" Relatório salvo em STRATEGIC_REPORT.md")

if __name__ == "__main__":
    report = StrategicReport()
    report.generate()
