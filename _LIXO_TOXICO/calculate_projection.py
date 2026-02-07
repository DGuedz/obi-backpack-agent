
import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

def calculate_potential():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    print("Fetching data...", flush=True)
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    print(f"Positions: {len(positions)}", flush=True)
    
    total_potential_profit = 0
    total_risk = 0
    
    print("\n PROJEÇÃO DE LUCRO (CENÁRIO IDEAL)")
    print("=======================================")
    
    for p in positions:
        symbol = p['symbol']
        qty = float(p['netQuantity'])
        if qty == 0: continue
        
        entry = float(p['entryPrice'])
        side = "LONG" if qty > 0 else "SHORT"
        abs_qty = abs(qty)
        
        # Find TP and SL
        tp_order = next((o for o in orders if o['symbol'] == symbol and o['orderType'] == 'Limit' and o['triggerPrice'] is None), None)
        sl_order = next((o for o in orders if o['symbol'] == symbol and o['triggerPrice'] is not None), None)
        
        profit = 0
        risk = 0
        
        print(f"\n {symbol} ({side})")
        
        if tp_order:
            tp_price = float(tp_order['price'])
            if side == "LONG":
                profit = (tp_price - entry) * abs_qty
            else:
                profit = (entry - tp_price) * abs_qty
            print(f"    Alvo: ${tp_price:.4f} | Potencial: +${profit:.2f}")
            total_potential_profit += profit
        else:
            print("   ️ Sem TP definido (Potencial Indefinido)")
            
        if sl_order:
            sl_price = float(sl_order['triggerPrice'])
            if side == "LONG":
                risk = (entry - sl_price) * abs_qty
            else:
                risk = (sl_price - entry) * abs_qty
            print(f"    Stop: ${sl_price:.4f} | Risco: -${risk:.2f}")
            total_risk += risk
        else:
             print("   ️ Sem SL definido (Risco Infinito!)")

    # Farm Projection
    # 10 Trades, 7 Wins ($2.80), 3 Losses ($4.80)
    farm_proj = (7 * 2.80) - (3 * 4.80)
    
    print("\n SCALP FARM (PROJEÇÃO NOTURNA)")
    print(f"   Estimativa (10 Trades, 70% Win): +${farm_proj:.2f}")
    
    grand_total = total_potential_profit + farm_proj
    
    print("\n=======================================")
    print(f" LUCRO TOTAL ESTIMADO: +${grand_total:.2f}")
    print(f"️ RISCO MÁXIMO (STOPS): -${total_risk:.2f}")
    print(f"️ RELAÇÃO RISCO/RETORNO: {grand_total/total_risk:.2f}x" if total_risk > 0 else "N/A")
    print("=======================================")

if __name__ == "__main__":
    calculate_potential()
