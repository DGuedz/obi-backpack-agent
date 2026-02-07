
import os
import sys
import json
from dotenv import load_dotenv

# Configura path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega env vars
load_dotenv()

from core.backpack_transport import BackpackTransport

def monitor_prediction_pnl():
    transport = BackpackTransport()
    print(" OBI PREDICTION PnL MONITOR")
    
    # Nossas Posições (Hardcoded baseado na execução anterior para este exemplo)
    # Num sistema completo, leríamos do banco de dados ou histórico de ordens
    portfolio = [
        {"symbol": "FDVEXTD800M_USDC_PREDICTION", "entry_price": 0.181, "qty": 11, "name": "Extended > 800M"},
        {"symbol": "FDVPARA1N5B_USDC_PREDICTION", "entry_price": 0.039, "qty": 39, "name": "Paradex > 1.5B"},
        {"symbol": "FDVEDGEX4B_USDC_PREDICTION", "entry_price": 0.039, "qty": 39, "name": "edgeX > 4B"}
    ]
    
    print("\n⏳ Fetching live prices...")
    markets = transport.get_prediction_markets()
    if not markets:
        print("    Error fetching markets.")
        return

    # Flatten markets for lookup
    market_map = {}
    for m in markets:
        for pm in m.get('predictionMarkets', []):
            market_map[pm.get('marketSymbol')] = float(pm.get('activePrice') or 0)

    total_invested = 0.0
    total_current_value = 0.0
    
    print(f"\n{'POSIÇÃO':<25} | {'ENTRADA':<8} | {'ATUAL':<8} | {'ROI':<8} | {'PnL ($)':<8}")
    print("-" * 70)
    
    for pos in portfolio:
        current_price = market_map.get(pos['symbol'], 0.0)
        invested = pos['entry_price'] * pos['qty']
        current_val = current_price * pos['qty']
        
        pnl = current_val - invested
        roi = (pnl / invested) * 100 if invested > 0 else 0
        
        total_invested += invested
        total_current_value += current_val
        
        color = "🟢" if pnl >= 0 else ""
        print(f"{color} {pos['name']:<22} | ${pos['entry_price']:.3f}   | ${current_price:.3f}   | {roi:+.1f}%   | ${pnl:+.2f}")
        
    print("-" * 70)
    total_pnl = total_current_value - total_invested
    total_roi = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    print(f" TOTAL INVESTIDO: ${total_invested:.2f}")
    print(f" VALOR ATUAL:     ${total_current_value:.2f}")
    print(f" PnL TOTAL:       ${total_pnl:+.2f} ({total_roi:+.2f}%)")

    # Philosophy Check
    if total_roi > 5.0:
        print("\n ALERTA: ROI > 5% atingido! Considere realizar lucro parcial.")
    elif total_roi < -10.0:
        print("\n️ ALERTA: Drawdown > 10%. Mantenha a calma, são posições de valor.")

if __name__ == "__main__":
    monitor_prediction_pnl()
