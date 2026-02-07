import os
import sys
import time
import datetime
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

# --- Configuração ---
WATCHLIST = ["PENGU_USDC_PERP", "HYPE_USDC_PERP", "ETH_USDC_PERP"]
SL_PERCENT = 0.02
TP_PERCENT = 0.05

def guardian_loop():
    print(f" GUARDIAN ANGEL ATIVADO - Monitorando {WATCHLIST}...")
    
    api_key = os.getenv('BACKPACK_API_KEY')
    private_key = os.getenv('BACKPACK_API_SECRET')
    
    if not api_key:
        print(" API Key missing")
        return

    auth = BackpackAuth(api_key, private_key)
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    
    # Cache para evitar spam de logs
    last_status = {}

    while True:
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            # print(f"[{timestamp}]  Escaneando posições...", end='\r')
            
            positions = data.get_positions()
            open_orders = data.get_open_orders()
            
            for symbol in WATCHLIST:
                # 1. Verificar se temos Posição Aberta
                position = next((p for p in positions if p['symbol'] == symbol and float(p['quantity']) != 0), None)
                
                if position:
                    qty = float(position['quantity'])
                    entry_price = float(position['entryPrice'])
                    side = "Long" if qty > 0 else "Short"
                    
                    # 2. Verificar se já existem ordens de proteção (SL e TP)
                    symbol_orders = [o for o in open_orders if o['symbol'] == symbol]
                    
                    has_sl = any(o.get('orderType') in ['StopLimit', 'StopMarket'] and o.get('reduceOnly') for o in symbol_orders)
                    has_tp = any(o.get('orderType') == 'Limit' and o.get('reduceOnly') for o in symbol_orders)
                    
                    status_key = f"{symbol}_{has_sl}_{has_tp}"
                    if status_key != last_status.get(symbol):
                        print(f"\n[{timestamp}]  POSIÇÃO DETECTADA EM {symbol} ({side})")
                        print(f"   Entrada: {entry_price} | Qty: {qty}")
                        print(f"   Status: SL={'' if has_sl else ''} | TP={'' if has_tp else ''}")
                        last_status[symbol] = status_key
                    
                    # 3. AGIR: Se faltar SL ou TP, colocar imediatamente
                    if not has_sl:
                        print(f"   ️ STOP LOSS AUSENTE! CALCULANDO E ENVIANDO...")
                        
                        # Cálculo SL
                        if side == "Long":
                            sl_price = entry_price * (1 - SL_PERCENT)
                            trigger_price = entry_price * (1 - SL_PERCENT + 0.0005) # Um pouco antes
                        else:
                            sl_price = entry_price * (1 + SL_PERCENT)
                            trigger_price = entry_price * (1 + SL_PERCENT - 0.0005)
                            
                        # Ajustar precisão (importante!)
                        # ... (simplificado para float str por enquanto, ideal é pegar tickSize)
                        # Vamos usar formatação segura de 5 casas decimais ou baseada no preço
                        decimals = 6 if entry_price < 1 else 2
                        sl_price_str = f"{sl_price:.{decimals}f}"
                        trigger_str = f"{trigger_price:.{decimals}f}"
                        
                        print(f"   ️ Enviando SL Trigger: {trigger_str} | Price: {sl_price_str}")
                        
                        res = trade.execute_order(
                            symbol=symbol,
                            side="Ask" if side == "Long" else "Bid",
                            price=sl_price_str,
                            quantity=abs(qty), # Stop cobre tudo
                            order_type="Limit", # Trigger Limit
                            trigger_price=trigger_str,
                            reduce_only=True
                        )
                        if res: print(f"    SL ENVIADO! ID: {res.get('id')}")
                    
                    if not has_tp:
                        print(f"   ️ TAKE PROFIT AUSENTE! CALCULANDO E ENVIANDO...")
                        
                        # Cálculo TP
                        if side == "Long":
                            tp_price = entry_price * (1 + TP_PERCENT)
                        else:
                            tp_price = entry_price * (1 - TP_PERCENT)
                            
                        decimals = 6 if entry_price < 1 else 2
                        tp_price_str = f"{tp_price:.{decimals}f}"
                        
                        print(f"    Enviando TP Limit: {tp_price_str}")
                        
                        res = trade.execute_order(
                            symbol=symbol,
                            side="Ask" if side == "Long" else "Bid",
                            price=tp_price_str,
                            quantity=abs(qty),
                            order_type="Limit",
                            reduce_only=True
                        )
                        if res: print(f"    TP ENVIADO! ID: {res.get('id')}")

                else:
                    # Sem posição aberta (pode ser ordem pendente)
                    # Verificar se temos ordens Limit (Entrada) pendentes
                    limit_orders = [o for o in open_orders if o['symbol'] == symbol and o['orderType'] == 'Limit' and not o.get('reduceOnly')]
                    if limit_orders:
                        if last_status.get(symbol) != "PENDING":
                            print(f"[{timestamp}] ⏳ {symbol}: Aguardando execução da ordem Limit (Entry)...")
                            last_status[symbol] = "PENDING"
            
            time.sleep(5) # Verificar a cada 5 segundos
            
        except Exception as e:
            print(f"Erro no loop Guardian: {e}")
            time.sleep(5)

if __name__ == "__main__":
    guardian_loop()
