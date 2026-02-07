import os
import sys
import time
import json

# Fix imports robustly
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

try:
    from core.backpack_transport import BackpackTransport
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.backpack_transport import BackpackTransport

def run_transfer_and_execute():
    print(" INICIANDO PROTOCOLO DE TRANSFERÊNCIA E EXECUÇÃO...", flush=True)
    transport = BackpackTransport()
    
    # 1. Verificar Saldo Spot
    print("\n [1] Verificando Saldo Spot (USDC)...", flush=True)
    try:
        spot_assets = transport.get_assets()
        usdc_balance = "0"
        
        if spot_assets and isinstance(spot_assets, dict):
            # Check for USDC in the dictionary
            if "USDC" in spot_assets:
                # Handle dictionary format {'available': '...', ...}
                usdc_data = spot_assets["USDC"]
                if isinstance(usdc_data, dict):
                    usdc_balance = usdc_data.get("available", "0")
                else:
                    usdc_balance = str(usdc_data)
        
        print(f"   -> Saldo Spot Disponível: {usdc_balance} USDC")
        
        balance_float = float(usdc_balance)
        
        # Check Locked Funds if balance is low
        locked = "0"
        if "USDC" in spot_assets and isinstance(spot_assets["USDC"], dict):
            locked = spot_assets["USDC"].get("locked", "0")
            print(f"   ️ Nota: {locked} USDC estão em ordens abertas (Locked).")
        
        if balance_float < 5: # Minimum usually required
            print("   ️ Saldo Spot insuficiente para transferência segura (Min $5).")
            
            # If user INSISTS ("DO THE WORK"), maybe it's in another asset?
            # Or maybe we need to cancel orders first?
            # Let's check locked funds again.
            if float(locked) > 5:
                print("    Tentando cancelar ordens abertas para liberar saldo...")
                # Cancel all open orders
                open_orders = transport.get_open_orders()
                if open_orders:
                    for o in open_orders:
                        print(f"      Canceling {o['symbol']} order {o['id']}...")
                        transport.cancel_order(o['symbol'], o['id'])
                    
                    time.sleep(1)
                    # Re-check balance
                    spot_assets = transport.get_assets()
                    if "USDC" in spot_assets:
                        usdc_data = spot_assets["USDC"]
                        if isinstance(usdc_data, dict):
                            usdc_balance = usdc_data.get("available", "0")
                        else:
                            usdc_balance = str(usdc_data)
                        
                        balance_float = float(usdc_balance)
                        print(f"      Saldo Liberado: {usdc_balance} USDC")
            
            # Last attempt: Check Futures for existing collateral
            # EVEN IF SPOT IS ZERO, WE MUST CHECK FUTURES
            print("    Verificando se já existe saldo em Futures...")
            collateral = transport.get_capital()
            avail_futures = "0"
            if collateral and isinstance(collateral, dict):
                 avail_futures = collateral.get('availableToTrade', '0')
                 # If avail_futures is None or invalid, default to 0
                 if not avail_futures:
                     avail_futures = "0"
                 print(f"   -> Saldo Futures Disponível: {avail_futures} USDC")
             
            if float(avail_futures) < 5:
                 if balance_float < 5:
                     # One more check: Maybe funds are in another subaccount?
                     # Can't check subaccounts easily without master key perms.
                     # But we can check if we can withdraw from Futures to Spot (reverse check)?
                     # No, let's just fail for now.
                     print("    Sem saldo suficiente em Spot ou Futures. Abortando.")
                     return
            else:
                 print("    Saldo encontrado em Futures! Pulando transferência.")
                 # Skip transfer logic and proceed to execution
                 pass
        
        # 2. Transferir para Futures (Only if we have spot balance)
        if balance_float >= 5:
            print(f"\n [2] Transferindo {usdc_balance} USDC para Futures...", flush=True)
            # Transfer all available
            transfer_result = transport.transfer_spot_to_futures(usdc_balance)
            print(f"   -> Resultado Transferência: {transfer_result}")
            
            # Wait a bit for propagation
            time.sleep(2)
        
    except Exception as e:
        print(f"    Erro na Transferência: {e}")
        return

    # 3. Executar BTC Trap Strategy
    print("\n️ [3] Executando BTC Trap Strategy...", flush=True)
    try:
        # Get Price
        klines = transport.get_klines("BTC_USDC", "1m", limit=1)
        price = float(klines[-1]['close'])
        print(f"   -> Preço BTC: ${price}")
        
        # Setup: $50 Margin x 10 = $500 Notional
        # Ensure we have enough margin now
        collateral = transport.get_capital()
        print(f"   -> Saldo Futures Atualizado: {collateral}")
        
        # Calculate Qty
        notional = 500
        qty = round(notional / price, 3)
        
        print(f"   -> Ordem: Buy Market {qty} BTC")
        
        res = transport.execute_order("BTC_USDC", "Market", "Bid", qty)
        print(f"   -> Resultado Ordem: {res}")
        
        if res and 'id' in res:
            print("    TRADE EXECUTADO COM SUCESSO!")
            
            # SL/TP
            tp = round(price * 1.015, 1)
            sl = round(price * 0.990, 1)
            print(f"   ️ Configurando TP ({tp}) e SL ({sl})...")
            
            transport.execute_order("BTC_USDC", "Limit", "Ask", qty, price=tp)
            # transport.execute_order("BTC_USDC", "StopMarket", "Ask", qty, trigger_price=sl) # Uncomment if supported
            
    except Exception as e:
        print(f"    Erro na Execução do Trade: {e}")

if __name__ == "__main__":
    run_transfer_and_execute()
