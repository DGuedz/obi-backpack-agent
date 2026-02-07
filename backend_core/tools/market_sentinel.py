import time
import os
import sys
import asyncio
from datetime import datetime
from termcolor import colored
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Configurações
CHECK_INTERVAL = 30  # Segundos
OBI_ALERT_THRESHOLD = 0.5
SCORE_ALERT_THRESHOLD = 50

# Watchlist Prioritária (Baseada na conversa)
WATCHLIST = [
    "BTC_USDC_PERP", 
    "ETH_USDC_PERP", 
    "SOL_USDC_PERP", 
    "AVAX_USDC_PERP",
    "HYPE_USDC_PERP",
    "SEI_USDC_PERP"
]

def log_alert(symbol, obi, score, pulse, price):
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if obi > 0:
        direction = colored("BULLISH 🟢", "green", attrs=["bold"])
    else:
        direction = colored("BEARISH ", "red", attrs=["bold"])
        
    msg = f"[{timestamp}]  SINAL CLARO: {symbol} | OBI: {obi:+.2f} | Score: {score:.1f} | {direction} @ {price}"
    print(colored("="*len(msg), "yellow"))
    print(msg)
    print(colored("="*len(msg), "yellow"))

def main():
    load_dotenv()
    print(colored("\n MARKET SENTINEL INICIADO", "cyan", attrs=["bold"]))
    print(f"   -> Monitorando Watchlist: {', '.join(WATCHLIST)}")
    print(f"   -> Alerta se OBI > {OBI_ALERT_THRESHOLD} ou Score > {SCORE_ALERT_THRESHOLD}")
    print(colored("   -> Aguardando sinais claros...\n", "cyan"))
    
    # Check if keys exist
    key = os.getenv('BACKPACK_API_KEY')
    secret = os.getenv('BACKPACK_API_SECRET')
    if not key or not secret:
        print(colored(" ERRO: Chaves de API não encontradas no .env", "red"))
        return

    auth = BackpackAuth(key, secret)
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    # Cache simples para não spammar o mesmo alerta
    last_alert = {}
    
    while True:
        try:
            pulse = oracle.get_market_pulse()
            print(f"\r⏳ Scanning... (Pulse: {pulse})", end="", flush=True)
            
            for symbol in WATCHLIST:
                try:
                    # Dados Rápidos
                    ticker = data_client.get_ticker(symbol)
                    price = float(ticker['lastPrice'])
                    depth = data_client.get_orderbook_depth(symbol)
                    
                    # Cálculos
                    obi = oracle.calculate_obi(depth)
                    
                    # Spread/Score simplificado para rapidez
                    best_bid = float(depth['bids'][-1][0])
                    best_ask = float(depth['asks'][0][0])
                    spread_pct = (best_ask - best_bid) / best_bid
                    
                    score = (abs(obi) * 100) / (spread_pct * 10000 + 1)
                    
                    # Lógica de Alerta
                    is_clear_signal = abs(obi) >= OBI_ALERT_THRESHOLD or score >= SCORE_ALERT_THRESHOLD
                    
                    # Debounce de 5 minutos por símbolo
                    last_ts = last_alert.get(symbol, 0)
                    now_ts = time.time()
                    
                    if is_clear_signal and (now_ts - last_ts > 300):
                        print("\r" + " "*50 + "\r", end="") # Limpar linha
                        log_alert(symbol, obi, score, pulse, price)
                        last_alert[symbol] = now_ts
                        
                except Exception as e:
                    continue
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n Sentinela Parado.")
            break
        except Exception as e:
            print(f"\n️ Erro no Loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
