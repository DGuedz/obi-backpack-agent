
import os
import sys
import asyncio
import time
from datetime import datetime
from colorama import Fore, Style, init
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.technical_oracle import TechnicalOracle

# Init colorama
init(autoreset=True)

async def obi_matrix_monitor():
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    targets = [
        "BTC_USDC_PERP", 
        "ETH_USDC_PERP", 
        "SOL_USDC_PERP", 
        "HYPE_USDC_PERP", 
        "DOGE_USDC_PERP",
        "SUI_USDC_PERP"
    ]
    
    print(f"{Fore.CYAN}\n OBI INTELLIGENCE MONITOR (Micro-Context Filter){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Escaneando o fluxo de ordens em tempo real. OBI > 0.3 = Gatilho.{Style.RESET_ALL}")
    print("-" * 100)
    print(f"{'TIME':<10} | {'SYMBOL':<15} | {'PRICE':<10} | {'OBI SCORE':<10} | {'INTENSITY':<20} | {'SIGNAL':<10}")
    print("-" * 100)
    
    try:
        while True:
            for symbol in targets:
                try:
                    depth = data_client.get_orderbook_depth(symbol)
                    if not depth: continue
                    
                    # 1. Calcular OBI (Instantâneo)
                    obi = oracle.calculate_obi(depth, detect_spoofing=True)
                    
                    # 2. Calcular Tendência 15m (Contexto)
                    klines = data_client.get_klines(symbol, "15m", limit=50)
                    trend_15m = "NEUTRAL"
                    if klines:
                        import pandas as pd
                        df = pd.DataFrame(klines)
                        df['close'] = df['close'].astype(float)
                        ema_20 = df['close'].ewm(span=20, adjust=False).mean().iloc[-1]
                        current_price = df['close'].iloc[-1]
                        
                        if current_price > ema_20: trend_15m = f"{Fore.GREEN}BULL (15m){Style.RESET_ALL}"
                        else: trend_15m = f"{Fore.RED}BEAR (15m){Style.RESET_ALL}"

                    # Preço Atual
                    best_bid = float(depth['bids'][-1][0])
                    
                    # Visualização da Intensidade
                    bar_len = 10
                    fill = int(abs(obi) * bar_len)
                    
                    if obi > 0:
                        bar = f"{Fore.GREEN}{'█' * fill}{Fore.RESET}{'░' * (bar_len - fill)}"
                        obi_fmt = f"{Fore.GREEN}+{obi:.2f}{Style.RESET_ALL}"
                    else:
                        bar = f"{Fore.RED}{'█' * fill}{Fore.RESET}{'░' * (bar_len - fill)}"
                        obi_fmt = f"{Fore.RED}{obi:.2f}{Style.RESET_ALL}"
                        
                    # Sinal de Gatilho
                    signal = "-"
                    if obi > 0.3: signal = f"{Fore.GREEN}LONG {Style.RESET_ALL}"
                    elif obi < -0.3: signal = f"{Fore.RED}SHORT {Style.RESET_ALL}"
                    
                    # Timestamp
                    now = datetime.now().strftime("%H:%M:%S")
                    
                    # Só imprime se tiver sinal relevante para reduzir ruído
                    # Ou se o usuário pediu (neste caso, mostra tudo para ver o contexto)
                    print(f"{now:<10} | {symbol:<15} | {best_bid:<10.4f} | {trend_15m:<20} | {obi_fmt:<19} | {bar:<29} | {signal:<10}")
                        
                except Exception as e:
                    pass
            
            # Rate Limit Friendly
            await asyncio.sleep(2) 
            
    except KeyboardInterrupt:
        print("\n Monitor OBI encerrado.")

if __name__ == "__main__":
    asyncio.run(obi_matrix_monitor())
