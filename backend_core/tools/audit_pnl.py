import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth

# Configurar Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("AuditPnL")

class PnLAuditor:
    def __init__(self):
        load_dotenv()
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))

    async def audit(self):
        print("️  AUDITORIA DE PNL REAL & MARGENS")
        print("--------------------------------------------------")
        
        # 1. Obter Saldo Atual
        balance = self.transport.get_account_collateral()
        usdc_bal = 0
        if balance and 'USDC' in balance:
             usdc_bal = balance['USDC'].get('availableToTrade', 0)
        
        print(f" Saldo Atual (USDC): ${float(usdc_bal):.2f}")
        
        # 2. Obter Histórico de Fills (Últimos 100)
        # Nota: A API da Backpack retorna fills. Precisamos agrupar por Trade ou analisar individualmente.
        print(" Buscando histórico de execuções...")
        fills = self.transport.get_fill_history(limit=100) # Assumindo que este método existe ou equivalente
        
        if not fills:
            print(" Sem histórico recente encontrado.")
            return

        # Análise de Margem
        total_fees = 0
        total_pnl_realized = 0
        winning_trades = 0
        losing_trades = 0
        
        print(f"\n Últimos 10 Trades (Mais recentes primeiro):")
        print(f"{'Data':<10} | {'Symbol':<15} | {'Side':<5} | {'Size ($)':<8} | {'Fee ($)':<8} | {'PnL ($)':<8} | {'Net ($)':<8}")
        print("-" * 80)
        
        for fill in fills[:20]: # Analisar os 20 últimos
            symbol = fill.get('symbol')
            side = fill.get('side')
            price = float(fill.get('price'))
            qty = float(fill.get('quantity'))
            fee = float(fill.get('fee', 0))
            pnl = float(fill.get('realizedPnl', 0)) # Nem sempre disponível no fill, depende da API
            
            # Se PnL não vier no fill, precisamos estimar ou buscar de outra endpoint 'get_pnl_history'
            # Vamos assumir que 'fee' está correto.
            
            notional = price * qty
            net_result = pnl - fee
            
            total_fees += fee
            total_pnl_realized += pnl
            
            if pnl > 0: winning_trades += 1
            elif pnl < 0: losing_trades += 1
            
            # Destaque visual
            pnl_str = f"${pnl:.2f}"
            net_str = f"${net_result:.2f}"
            
            if net_result > 0:
                net_str = f" {net_str}"
            elif net_result < 0:
                net_str = f" {net_str}"
                
            timestamp = fill.get('timestamp', '') # Converter se necessário
            
            print(f"{timestamp[:10]:<10} | {symbol:<15} | {side:<5} | {notional:<8.1f} | {fee:<8.3f} | {pnl_str:<8} | {net_str:<8}")

        print("-" * 80)
        print(f"\n RESUMO DA SESSÃO (Amostra):")
        print(f"   Trades Analisados: {min(len(fills), 20)}")
        print(f"   Taxas Pagas:      ${total_fees:.4f}")
        print(f"   PnL Bruto:        ${total_pnl_realized:.4f}")
        print(f"   ---------------------------")
        print(f"   LUCRO LÍQUIDO:    ${total_pnl_realized - total_fees:.4f}")
        
        if total_fees > total_pnl_realized and total_pnl_realized > 0:
            print("\n️  ALERTA CRÍTICO: AS TAXAS ESTÃO COMENDO TODO O LUCRO!")
            print("   Recomendação: Aumentar Meta de Lucro Mínima ou Usar Apenas Maker.")

if __name__ == "__main__":
    auditor = PnLAuditor()
    asyncio.run(auditor.audit())
