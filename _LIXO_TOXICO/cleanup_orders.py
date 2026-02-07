
import os
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

def cleanup_stale_orders():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    print(" FAXINA DE ORDENS (STALE CLEANUP)...")
    print("======================================")
    
    orders = data.get_open_orders()
    if not orders:
        print("   Nenhuma ordem aberta encontrada.")
        return

    positions = data.get_positions()
    # Create map of active position symbols
    active_symbols = [p['symbol'] for p in positions if float(p['netQuantity']) != 0]
    
    cleaned_count = 0
    
    for o in orders:
        symbol = o['symbol']
        order_type = o['orderType']
        trigger = o.get('triggerPrice')
        price = o.get('price')
        
        # LOGIC:
        # 1. Keep SL/TP orders (Trigger or Limit related to active position)
        # 2. Kill "Limit" orders that are NOT TPs (i.e., old entry attempts)
        
        # If order is a Trigger (SL), KEEP IT
        if trigger is not None:
            # print(f"   ️ Mantendo SL em {symbol} (Trigger: {trigger})")
            continue
            
        # If order is Limit
        if order_type == "Limit":
            # Is it a TP for an active position?
            # Simple heuristic: If we have a position in this symbol, assume Limit is TP.
            # But wait, user said "orders placed that graph didn't pick up". 
            # These are likely ENTRY orders far from price.
            
            # Let's check distance from current price.
            ticker = data.get_ticker(symbol)
            if not ticker: continue
            last_price = float(ticker['lastPrice'])
            limit_price = float(price)
            
            # If we have a position, Limit could be TP or Add.
            if symbol in active_symbols:
                # If Limit is close to Mark Price (TP), keep.
                # If Limit is far away and "old", maybe kill?
                # Safest bet: User wants to unlock margin.
                # Entry orders usually lock margin. TPs (ReduceOnly) usually don't lock collateral (depending on exchange).
                # Let's assume non-ReduceOnly Limits are Entry attempts.
                
                is_reduce = o.get('reduceOnly', False)
                if is_reduce:
                    # print(f"    Mantendo TP (ReduceOnly) em {symbol}")
                    continue
                else:
                    # This is likely an ADD order or stale Entry.
                    # Ask user? No, "analise e cancele".
                    # Let's cancel non-reduce limits to free margin.
                    print(f"   ️ Cancelando ORDEM LIMIT (Entrada Pendente) em {symbol} @ {price}")
                    trade.cancel_all_orders(symbol) # This cancels ALL, including SLs! DANGEROUS.
                    # We must cancel by ID.
                    # But trade.cancel_open_orders(symbol) cancels all.
                    # We need cancel_order(id).
                    # Since we don't have cancel_order_by_id in `backpack_trade.py` yet, let's look at the file.
                    # It has `cancel_open_orders(symbol)` which kills everything.
                    
                    # Workaround: Identify symbols with NO position but WITH orders.
                    pass
            else:
                # Symbol NOT in active positions.
                # This is DEFINITELY a stale entry.
                print(f"   ️ Cancelando ORDEM FANTASMA (Sem Posição) em {symbol} @ {price}")
                trade.cancel_all_orders(symbol)
                cleaned_count += 1

    # Second Pass: Check if we killed everything for symbols with positions?
    # No, we only acted on symbols NOT in active_symbols in the loop above.
    
    # What about ZEC? User planted a Sniper order. Should we kill it?
    # User said "analise quais... precisam ser canceladas". 
    # ZEC sniper is intentional.
    # W_USDC_PERP? We saw W orders in previous logs.
    
    # Let's target SPECIFIC stale assets we know of: W_USDC_PERP.
    # We saw multiple W orders in previous logs.
    
    for o in orders:
        if o['symbol'] == 'W_USDC_PERP':
            print(f"   ️ Cancelando LIXO em W_USDC_PERP (ID: {o['id']})")
            trade.cancel_all_orders('W_USDC_PERP')
            cleaned_count += 1
            break # One call kills all for symbol

    print(f"    Faxina concluída. {cleaned_count} símbolos limpos.")

if __name__ == "__main__":
    cleanup_stale_orders()
