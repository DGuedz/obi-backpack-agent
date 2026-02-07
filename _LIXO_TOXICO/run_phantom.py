import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from phantom_hft import PhantomHFT

load_dotenv()

def run_phantom_scan():
    print(" PHANTOM HFT: Iniciando varredura de Liquidez e FVG...")
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    phantom = PhantomHFT(data)
    
    # Lista de ativos para escanear (Alta Volatilidade)
    watchlist = ["SOL_USDC_PERP", "ETH_USDC_PERP", "HYPE_USDC_PERP", "PENGU_USDC_PERP", "BTC_USDC_PERP", "DOGE_USDC_PERP"]
    
    print(f" Alvos: {watchlist}")
    print("-" * 60)
    
    found_any = False
    
    for symbol in watchlist:
        # print(f"Scanning {symbol}...", end='\r')
        setup = phantom.check_hft_scalp_setup(symbol, timeframe='5m')
        
        if setup:
            found_any = True
            direction = "🟢 LONG" if setup['signal'] == "LONG" else " SHORT"
            pnl_potential = abs(setup['target'] - setup['entry_price']) / setup['entry_price'] * 100
            
            print(f"\n SETUP ENCONTRADO EM {symbol}!")
            print(f"   Sinal: {direction}")
            print(f"   Motivo: {setup['reason']}")
            print(f"   Swing Point Varrido: {setup['swing_point']}")
            print(f"   Entry (Ref): {setup['entry_price']}")
            print(f"   Stop Loss (Wick): {setup['stop_loss']}")
            print(f"   Alvo (FVG): {setup['target']} (+{pnl_potential:.2f}%)")
            
            if pnl_potential < 0.35:
                print("   ️ ALERTA: Potencial < 0.35%. Risco de taxas. Ignorar.")
            else:
                print("    SETUP VIÁVEL. Executar Maker Only.")
    
    if not found_any:
        print("\n Nenhum setup de varredura (Sweep) confirmado no momento.")
        print("   O mercado pode estar em tendência (Breakout) ou lateral sem violação.")

if __name__ == "__main__":
    run_phantom_scan()
