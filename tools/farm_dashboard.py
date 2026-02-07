import os
import sys
import time
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport

def farm_dashboard():
    load_dotenv()
    transport = BackpackTransport()
    
    print("\n FARM DASHBOARD - VOLUME & PNL")
    print("=" * 60)
    
    # 1. Posições Ativas
    positions = transport.get_positions()
    active_df = []
    if positions:
        for p in positions:
            symbol = p['symbol']
            qty = float(p['netQuantity'])
            entry = float(p['entryPrice'])
            side = "LONG" if qty > 0 else "SHORT"
            notional = abs(qty * entry)
            
            # Ticker para PnL não realizado
            ticker = transport.get_ticker(symbol)
            curr_price = float(ticker['lastPrice']) if ticker else entry
            pnl_pct = ((curr_price - entry) / entry) * 100 if side == "LONG" else ((entry - curr_price) / entry) * 100
            
            active_df.append({
                "Symbol": symbol,
                "Side": side,
                "Size": f"${notional:.0f}",
                "Entry": entry,
                "PnL %": f"{pnl_pct:+.2f}%",
                "Status": " HARVESTING"
            })
    
    if active_df:
        print("\n POSIÇÕES ATIVAS (FROTA):")
        print(pd.DataFrame(active_df).to_string(index=False))
    else:
        print("\n FROTA AGUARDANDO ENTRADA (SCANNING)...")

    # 2. Histórico Recente (Volume Hoje) - Simulado/Estimado
    # A API de histórico de ordens pode ser pesada, vamos focar no estado atual.
    
    # 3. Métricas de Saúde
    print("-" * 60)
    print(" STATUS DO SISTEMA:")
    print("   -> Volume Farmer:    RUNNING (Terminal 13)")
    print("   -> Stealth Monitor:  RUNNING (Terminal 12)")
    print("   -> Estratégia:      MAKER ONLY + GREEN EXIT")
    print("=" * 60)

if __name__ == "__main__":
    while True:
        try:
            farm_dashboard()
            time.sleep(10) # Atualiza a cada 10s
            print("\n" * 2)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(5)