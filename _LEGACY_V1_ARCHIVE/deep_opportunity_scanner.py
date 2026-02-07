import time
import os
import pandas as pd
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_indicators import BackpackIndicators
from pre_flight_checklist import UltimateChecklist
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DO SETUP ---
LEVERAGE = 50
TARGET_TP_ROE = 30.0  # 30% ROE Target
TARGET_SL_PRICE_DIST = 0.01 # 1% Price Move (Safety Stop) -> 50% ROE Risk

# Price moves required for ROE targets at 50x
# TP Price Move = 30 / 50 = 0.6%
# SL Price Move = 1% (Fixed Distance)
REQ_MOVE_TP = TARGET_TP_ROE / LEVERAGE / 100
REQ_MOVE_SL = TARGET_SL_PRICE_DIST

def deep_opportunity_scanner():
    print(f"\n [DEEP DIVE] ANÁLISE ESTRUTURAL PARA SETUP 50X")
    print(f"    Alvo: Lucro {TARGET_TP_ROE}% ROE (Movimento {REQ_MOVE_TP*100:.2f}%)")
    print(f"   ️ Risco: Stop {TARGET_SL_PRICE_DIST*100:.1f}% Preço (Risco ROE {TARGET_SL_PRICE_DIST*LEVERAGE*100:.0f}%)")
    print(f"    Capital: 70% da Margem Disponível")
    print(f"    Filtro: Protocolo de 5 Camadas (Rigor Máximo)")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    indicators = BackpackIndicators()
    
    # 1. Filtro Inicial (Liquidez e Spread)
    print("\n    Varrendo Mercado (Filtro Preliminar)...")
    tickers = data.get_tickers()
    if not tickers:
        print("    Erro ao obter tickers.")
        return

    perp_tickers = [t for t in tickers if t['symbol'].endswith('_PERP')]
    
    candidates = []
    
    for t in perp_tickers:
        symbol = t['symbol']
        vol = float(t.get('quoteVolume', 0))
        
        # Filtro 1: Liquidez Mínima $1M (Para aguentar 50x sem slippage brutal)
        if vol < 1_000_000: continue
        
        # Filtro 2: Spread (Crítico para SL curto)
        # Se o spread for alto, comemos lucro na largada.
        best_bid = float(t.get('bestBid', t.get('lastPrice')))
        best_ask = float(t.get('bestAsk', t.get('lastPrice')))
        if best_bid == 0: continue
        
        spread = (best_ask - best_bid) / best_bid
        if spread > 0.0015: # Max 0.15% spread
            continue
            
        candidates.append(symbol)
        
    print(f"   ℹ️ {len(candidates)} ativos passaram no filtro de liquidez/spread.")
    print("    Iniciando Análise Profunda (5 Camadas) nos candidatos...")
    
    valid_opportunities = []
    
    for symbol in candidates:
        # Decidir Lado (Long ou Short) baseado em RSI rápido (Scan tático)
        try:
            # Pegar candles rapidinho para pré-decisão
            klines = data.get_klines(symbol, "1h", limit=50)
            if not klines: continue
            df = pd.DataFrame(klines)
            if df.empty: continue
            
            # RSI Calculation using BackpackIndicators
            df['rsi'] = indicators.calculate_rsi(df, window=14)
            rsi_val = df['rsi'].iloc[-1]
            
            direction = None
            if rsi_val < 35: direction = "Buy"   # Oversold -> Long (Relaxed slightly for scan)
            elif rsi_val > 65: direction = "Sell" # Overbought -> Short (Relaxed slightly for scan)
            
            if not direction: continue # Ignora meio de campo
            
            # --- EXECUÇÃO DO PROTOCOLO DE 5 CAMADAS ---
            print(f"\n   ️ Auditando {symbol} ({direction}) | RSI: {rsi_val:.2f}...")
            checklist = UltimateChecklist(symbol)
            approved, result = checklist.run_full_scan(direction, LEVERAGE)
            
            if not approved:
                print(f"       {result}")
                continue

            if approved:
                # Validar Volatilidade para o Setup
                # Precisamos que o ATR (volatilidade) suporte o movimento de TP (0.6%)
                atr = result['atr']
                price = result['entry_price']
                atr_pct = atr / price
                
                # Se o ATR de 1h for menor que o movimento do TP, vai demorar muito.
                # Se for muito maior, cuidado com violinada.
                print(f"       ATR (1h): {atr_pct*100:.2f}% (Req TP: {REQ_MOVE_TP*100:.2f}%)")
                
                if atr_pct < REQ_MOVE_TP:
                    print("      ️ ALERTA: Volatilidade baixa para o alvo. Pode demorar.")
                    # Mas não rejeita, pois o setup é swing/scalp misto
                    
                print(f"       OPORTUNIDADE VALIDADA: {symbol} {direction}")
                print(f"         Entrada: {price}")
                print(f"         Stop Loss (1%): {result['sl_price']} (Override Checklist SL se necessário)")
                
                valid_opportunities.append({
                    "symbol": symbol,
                    "side": direction,
                    "price": price,
                    "sl": result['sl_price'],
                    "rsi": rsi_val,
                    "atr_pct": atr_pct
                })
                
        except Exception as e:
            print(f"       Erro ao analisar {symbol}: {e}")
            continue

    print("\n" + "="*50)
    print(" RELATÓRIO FINAL DE OPORTUNIDADES (50x)")
    print("="*50)
    
    if not valid_opportunities:
        print(" Nenhuma oportunidade passou no Protocolo de 5 Camadas.")
    else:
        for op in valid_opportunities:
            print(f" {op['symbol']} [{op['side']}]")
            print(f"   RSI: {op['rsi']:.2f} | ATR: {op['atr_pct']*100:.2f}%")
            print(f"   Sugestão: 70% Capital | 50x | TP 30% ROE | SL 1% Move")
            print("-" * 30)

if __name__ == "__main__":
    deep_opportunity_scanner()
