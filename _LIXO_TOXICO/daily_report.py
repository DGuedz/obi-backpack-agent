#!/usr/bin/env python3
"""
 Daily Report - Audit & PnL Analysis
Levantamento financeiro preciso da operação Protocolo Omega.
"""

import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class DailyReport:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.STARTING_CAPITAL = 515.0 # Base pós-injeção estimada

    def generate(self):
        print("\n RELATÓRIO DE OPERAÇÕES - PROTOCOLO OMEGA")
        print("===========================================")
        
        try:
            # 1. Equity e Saldo
            collat = self.data.get_account_collateral()
            equity = float(collat.get('equity', 0))
            balance = float(collat.get('balance', 0))
            pnl_unrealized = float(collat.get('pnl', 0))
            
            # 2. Posições Abertas
            positions = self.data.get_positions()
            
            # 3. Volume Recente (Estimativa baseada em fills)
            # Pegar últimos 100 trades para sentir o pulso
            fills = self.data.get_fill_history(limit=100)
            recent_vol = 0.0
            fees_paid = 0.0
            
            if fills:
                for f in fills:
                    price = float(f.get('price', 0))
                    qty = float(f.get('quantity', 0))
                    fee = float(f.get('fee', 0))
                    recent_vol += (price * qty)
                    fees_paid += fee

            # Cálculos de Meta
            total_pnl = equity - self.STARTING_CAPITAL
            pnl_percent = (total_pnl / self.STARTING_CAPITAL) * 100
            
            target_1k_equity = 1000.0
            gap_to_target = target_1k_equity - equity
            
            print(f" CAPITAL TOTAL (Equity): ${equity:,.2f}")
            print(f"    Saldo em Wallet:     ${balance:,.2f}")
            print(f"    PnL Não Realizado:   ${pnl_unrealized:,.2f}")
            print("-" * 40)
            
            print(f" PERFORMANCE (Desde Injeção ~$515):")
            color = "🟢" if total_pnl >= 0 else ""
            print(f"   {color} Lucro/Prejuízo:     ${total_pnl:,.2f} ({pnl_percent:+.2f}%)")
            print(f"    Volume Recente (100 trades): ${recent_vol:,.2f}")
            print(f"    Taxas Pagas:         ${fees_paid:,.2f}")
            print("-" * 40)
            
            print("️ POSIÇÕES ATIVAS:")
            if positions:
                for p in positions:
                    side = "Long" if float(p.get('quantity', 0)) > 0 else "Short"
                    sym = p['symbol']
                    entry = float(p['entryPrice'])
                    mark = float(p['markPrice'])
                    lev = p.get('leverage', '?')
                    pnl_pos = float(p.get('pnl', 0))
                    
                    print(f"    {sym} ({side} {lev}x) | Entry: ${entry:.2f} | Mark: ${mark:.2f} | PnL: ${pnl_pos:.2f}")
            else:
                print("    Nenhuma posição aberta (Weaver/Phoenix aguardando).")
                
            print("-" * 40)
            print(" META $1,000 EQUITY:")
            if gap_to_target > 0:
                print(f"    Falta: ${gap_to_target:,.2f} para atingir $1,000 de Banca.")
                print(f"    Progresso: {(equity/target_1k_equity)*100:.1f}% concluído.")
            else:
                print("    META ATINGIDA! Próximo alvo: $2,000.")

        except Exception as e:
            print(f" Erro ao gerar relatório: {e}")

if __name__ == "__main__":
    report = DailyReport()
    report.generate()