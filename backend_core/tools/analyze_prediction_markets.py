import os
import sys
import json
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append("/Users/doublegreen/backpacktrading")
sys.path.append("/Users/doublegreen/backpacktrading/core")
sys.path.append("/Users/doublegreen/backpacktrading/_LEGACY_V1_ARCHIVE")

try:
    from backpack_transport import BackpackTransport
    from backpack_data import BackpackData
    from backpack_auth import BackpackAuth
    from technical_oracle import TechnicalOracle
except ImportError as e:
    print(f" Import Error: {e}")
    sys.exit(1)

def analyze_prediction_markets():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    print(" VARRENDO MERCADOS DISPONÍVEIS NA BACKPACK...")
    markets = data_client.get_markets()
    
    if not markets:
        print(" Falha ao obter mercados.")
        return

    # Palavras-chave para identificar mercados de predição ou tokens políticos/eventos
    prediction_keywords = ['TRUMP', 'HARRIS', 'BIDEN', 'VOTE', 'WIN', 'LOSE', 'PRED', 'POLY', 'HYPE', 'USDC_PERP']
    
    prediction_candidates = []
    
    for m in markets:
        symbol = m['symbol']
        # Filtrar apenas PERP para trading ou SPOT se for o caso
        # Vamos focar em encontrar qualquer coisa relacionada
        
        is_candidate = False
        # Verifica keywords
        for kw in prediction_keywords:
            if kw in symbol and 'USDC' in symbol: # Focando em pares USDC
                # HYPE já sabemos que é prediction market (Hyperliquid)
                # TRUMP/MAGA tokens políticos agem como prediction
                if kw == 'USDC_PERP': continue # Skip generic keyword for now, unless we want ALL perps
                is_candidate = True
                break
        
        # Adicionar manualmente HYPE se existir, pois é o principal
        if 'HYPE' in symbol:
            is_candidate = True
            
        if is_candidate:
            prediction_candidates.append(m)

    print(f" Encontrados {len(prediction_candidates)} candidatos a Mercados de Predição/Eventos.")
    
    # Se não achar nada específico, lista os Top Movers que podem ser "apostas" do dia
    if not prediction_candidates:
        print("️ Nenhum token de predição óbvio (TRUMP, HYPE, etc) encontrado pelo nome.")
        print("Listando todos os PERPs para análise manual de volatilidade (proxy de aposta)...")
        prediction_candidates = [m for m in markets if 'USDC_PERP' in m['symbol']]

    print("-" * 60)
    print(f"{'ATIVO':<15} | {'PREÇO':<9} | {'VOL 24H':<12} | {'OBI':<5} | {'FUNDING':<8} | {'PAREDE'}")
    print("-" * 60)

    transport = BackpackTransport()
    oracle = TechnicalOracle(data_client)
    
    for cand in prediction_candidates:
        symbol = cand['symbol']
        try:
            ticker = transport.get_ticker(symbol)
            if ticker:
                price = float(ticker['lastPrice'])
                vol = float(ticker['volume']) * price
                
                # Análise Profunda (apenas se tiver volume relevante > $10k)
                obi_str = "-"
                wall_str = "-"
                funding_str = "-"
                
                if vol > 10000:
                    # 1. OBI
                    depth = data_client.get_orderbook_depth(symbol)
                    if depth:
                        obi = oracle.calculate_obi(depth)
                        obi_str = f"{obi:.2f}"
                        
                        # Wall Check
                        bids_vol = sum([float(b[1]) for b in depth['bids'][:5]])
                        asks_vol = sum([float(a[1]) for a in depth['asks'][:5]])
                        if asks_vol > 0 and bids_vol / asks_vol > 2: wall_str = "BID (Buy)"
                        elif bids_vol > 0 and asks_vol / bids_vol > 2: wall_str = "ASK (Sell)"
                        else: wall_str = "Neutral"

                    # 2. Funding (Se for Perp)
                    if "PERP" in symbol:
                        # Tentar pegar funding (não temos endpoint direto no transport, vamos tentar inferir ou usar ticker data se disponivel)
                        # Na API da Backpack, funding rate costuma vir no ticker ou endpoint separado.
                        # Vamos tentar endpoint de markets ou ticker extendido.
                        # Por hora, deixamos funding vazio ou tentamos pegar de 'markPrice' vs 'lastPrice' spread como proxy
                        funding_str = "?" 
                        
                print(f"{symbol:<15} | ${price:<9.4f} | ${vol/1000:,.0f}k      | {obi_str:<5} | {funding_str:<8} | {wall_str}")
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
            
    print("-" * 60)
    print("LEGENDA: OBI > 0.3 (Compra Forte) | OBI < -0.3 (Venda Forte)")
    print("NOTA: 'HYPE' (Hyperliquid) é o principal proxy de Prediction Markets on-chain hoje.")

if __name__ == "__main__":
    analyze_prediction_markets()
