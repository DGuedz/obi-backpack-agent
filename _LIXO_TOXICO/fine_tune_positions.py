
import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

# Tuning Parameters (Day Mode)
SL_PCT = 0.012 # 1.2%
TP_PCT = 0.007 # 0.7%

def fine_tune():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    print(" INICIANDO SINTONIA FINA (FINE TUNING)...")
    print("===========================================")
    
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    if not positions:
        print("   Nenhuma posição ativa para ajustar.")
        return

    for p in positions:
        symbol = p['symbol']
        qty = float(p['netQuantity'])
        if qty == 0: continue
        
        entry = float(p['entryPrice'])
        side = "LONG" if qty > 0 else "SHORT"
        
        print(f"\n Analisando {symbol} ({side}) | Entry: {entry}")
        
        # Filter orders for this symbol
        sym_orders = [o for o in orders if o['symbol'] == symbol]
        
        has_sl = False
        has_tp = False
        
        # Analyze existing orders
        for o in sym_orders:
            # Check Limit TP
            if o['orderType'] == 'Limit' and o['triggerPrice'] is None:
                price = float(o['price'])
                # Validate direction
                if side == "LONG" and price > entry: has_tp = True
                if side == "SHORT" and price < entry: has_tp = True
                
            # Check Trigger (SL or TP Market)
            if o['triggerPrice'] is not None:
                trig = float(o['triggerPrice'])
                # SL Logic
                if side == "LONG":
                    if trig < entry: has_sl = True # SL below entry
                    elif trig > entry: has_tp = True # Trailing TP above entry
                elif side == "SHORT":
                    if trig > entry: has_sl = True # SL above entry
                    elif trig < entry: has_tp = True # Trailing TP below entry

        # Apply Tuning if missing
        exit_side = "Ask" if side == "LONG" else "Bid"
        abs_qty = abs(qty)
        
        # 1. Fix SL
        if not has_sl:
            print("   ️ SL NÃO DETECTADO (ou incorreto). Calculando nova proteção...")
            sl_price = entry * (1 - SL_PCT) if side == "LONG" else entry * (1 + SL_PCT)
            
            # Formatar preço (precisão básica, melhorar se necessário)
            if sl_price < 1: sl_str = f"{sl_price:.5f}"
            elif sl_price < 100: sl_str = f"{sl_price:.3f}"
            else: sl_str = f"{sl_price:.2f}"
            
            print(f"   ️ Aplicando SL em {sl_str}...")
            try:
                trade.execute_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="Market",
                    quantity=str(abs_qty),
                    price=None,
                    trigger_price=sl_str
                )
                print("       SL Configurado.")
            except Exception as e:
                print(f"       Falha ao aplicar SL: {e}")
        else:
            print("    SL Monitorado (Ok).")
            
        # 2. Fix TP
        if not has_tp:
            print("   ️ TP NÃO DETECTADO. Calculando alvo...")
            tp_price = entry * (1 + TP_PCT) if side == "LONG" else entry * (1 - TP_PCT)
            
            if tp_price < 1: tp_str = f"{tp_price:.5f}"
            elif tp_price < 100: tp_str = f"{tp_price:.3f}"
            else: tp_str = f"{tp_price:.2f}"
            
            print(f"    Aplicando TP em {tp_str}...")
            try:
                trade.execute_order(
                    symbol=symbol,
                    side=exit_side,
                    order_type="Limit",
                    quantity=str(abs_qty),
                    price=tp_str
                )
                print("       TP Configurado.")
            except Exception as e:
                print(f"       Falha ao aplicar TP: {e}")
        else:
            print("    TP Monitorado (Ok).")

if __name__ == "__main__":
    fine_tune()
