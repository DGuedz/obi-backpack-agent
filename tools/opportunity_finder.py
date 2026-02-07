import os
import sys
import asyncio
import time
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
sys.path.append(os.path.join(os.getcwd(), '_LIXO_TOXICO')) # Para acessar cmc_oracle.py

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle
from risk_manager import RiskManager
from cmc_oracle import CMCOracle

async def find_opportunities():
    load_dotenv()
    
    # 1. Consultar Macro (CMC)
    print("\n Consultando Macroeconomia (CMC)...", end="")
    cmc = CMCOracle()
    macro_data = cmc.get_global_metrics()
    
    macro_sentiment = "NEUTRAL"
    mcap_change = 0.0
    
    if macro_data:
        macro_sentiment = macro_data.get('sentiment', 'NEUTRAL')
        mcap_change = macro_data.get('mcap_change_24h', 0.0)
        print(f" Feito! [{macro_sentiment} | Mcap {mcap_change:+.2f}%]")
    else:
        print(" Falha (Ignorando Macro).")

    # 2. Inicializar Backpack
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    risk_manager = RiskManager(transport)
    
    # Parâmetros de Simulação de Alocação
    CAPITAL_PER_TRADE = 200.0 # $200 Margem
    LEVERAGE = 5              # 5x
    
    # Lista expandida para buscar oportunidades (Mercado Completo)
    targets = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
        "HYPE_USDC_PERP", "DOGE_USDC_PERP", "SUI_USDC_PERP",
        "AVAX_USDC_PERP", "LINK_USDC_PERP", "ARB_USDC_PERP",
        "TIA_USDC_PERP", "SEI_USDC_PERP", "OP_USDC_PERP",
        "APT_USDC_PERP", "JUP_USDC_PERP", "PYTH_USDC_PERP", 
        "WIF_USDC_PERP"
    ]
    
    opportunities = []
    
    # 0. BTC Correlation Check (Market Pulse)
    # Antes de tudo, analisamos o BTC. Se ele estiver muito Bearish, Longs em Alts são penalizados.
    btc_depth = data_client.get_orderbook_depth("BTC_USDC_PERP")
    btc_obi = oracle.calculate_obi(btc_depth) if btc_depth else 0
    btc_sentiment = "NEUTRAL"
    if btc_obi > 0.3: btc_sentiment = "BULLISH"
    elif btc_obi < -0.3: btc_sentiment = "BEARISH"
    
    print(f" BTC PULSE: {btc_sentiment} (OBI {btc_obi:+.2f})")
    print("-" * 135)
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'SPREAD%':<8} | {'OBI':<6} | {'SCORE':<6} | {'SAFE QTY':<10} | {'MAX CAPACITY($)':<16} | {'VERDICT':<10}")
    print("-" * 135)
    
    for symbol in targets:
        try:
            # 1. Spread (Custo)
            depth = data_client.get_orderbook_depth(symbol)
            if not depth or not depth['bids'] or not depth['asks']:
                continue
                
            best_bid = float(depth['bids'][-1][0])
            best_ask = float(depth['asks'][0][0])
            spread = best_ask - best_bid
            spread_pct = (spread / best_bid) * 100
            
            # 2. ATR (Potencial de Lucro)
            atr = oracle.get_atr(symbol, "15m", 14)
            atr_pct = (atr / best_bid) * 100
            
            # 3. OBI (Direção/Força)
            obi = oracle.calculate_obi(depth, detect_spoofing=True)
            
            # 4. Tendência (Filtro)
            klines = data_client.get_klines(symbol, "15m", limit=60)
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            trend = "BULL" if best_bid > ema_50 else "BEAR"
            
            # 5. Liquidity Sizing (Risk Manager)
            safe_qty = risk_manager.calculate_leveraged_position_size(
                usable_capital=CAPITAL_PER_TRADE, 
                leverage=LEVERAGE, 
                current_price=best_bid, 
                depth=depth
            )
            
            safe_alloc_usd = safe_qty * best_bid
            
            # CALCULAR CAPACIDADE MÁXIMA (Whale Limit)
            bids_vol = sum([float(x[1]) for x in depth.get('bids', [])[:5]])
            asks_vol = sum([float(x[1]) for x in depth.get('asks', [])[:5]])
            min_liquidity = min(bids_vol, asks_vol)
            max_capacity_qty = min_liquidity * 0.10
            max_capacity_usd = max_capacity_qty * best_bid
            
            liquidity_warning = "️ LIQ LIMIT" if safe_alloc_usd < (CAPITAL_PER_TRADE * LEVERAGE * 0.95) else " FULL"
            
            # 6. Score de Eficiência
            efficiency = atr_pct / spread_pct if spread_pct > 0 else 0
            
            # Penaliza OBI contra tendência
            obi_aligned = False
            if (trend == "BULL" and obi > 0) or (trend == "BEAR" and obi < 0):
                obi_aligned = True
                
            score = efficiency * abs(obi)
            if not obi_aligned: score = score * 0.1 # Penalidade severa se contra tendência
            
            # 7. FILTRO DE CORRELAÇÃO BTC (NOVO)
            # Se BTC Bearish e Alt Bullish -> Penalidade (Armadilha)
            # Se BTC Bullish e Alt Bearish -> Penalidade (Contra fluxo global)
            correlation_penalty = False
            if symbol != "BTC_USDC_PERP":
                if btc_sentiment == "BEARISH" and obi > 0:
                    score = score * 0.2 # Esmaga score de Long se BTC cai
                    correlation_penalty = True
                elif btc_sentiment == "BULLISH" and obi < 0:
                    score = score * 0.5 # Penaliza Short se BTC sobe (menos severo, Alts podem sangrar sozinhas)
                    correlation_penalty = True

            # Se Macro Bullish e OBI Bullish -> Boost
            if macro_sentiment == "BULLISH" and obi > 0.2:
                score *= 1.5
                print(f"    Macro Boost: Score aumentado em {symbol} (Macro Bullish)")
            elif macro_sentiment == "BEARISH" and obi < -0.2:
                score *= 1.5
                print(f"    Macro Boost: Score aumentado em {symbol} (Macro Bearish)")

            opportunities.append({
                "symbol": symbol,
                "price": best_bid,
                "spread_pct": spread_pct,
                "atr_pct": atr_pct,
                "obi": obi,
                "score": score,
                "trend": trend,
                "aligned": obi_aligned,
                "safe_qty": safe_qty,
                "safe_alloc_usd": safe_alloc_usd,
                "max_capacity_usd": max_capacity_usd,
                "liq_status": liquidity_warning,
                "btc_penalty": correlation_penalty
            })
            
        except Exception as e:
            # print(f"Erro em {symbol}: {e}")
            pass
            
    # Ordenar por Score
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    for op in opportunities:
        verdict = " SNIPER" if op['score'] > 50 and op['aligned'] else "️ WAIT"
        if op['score'] < 10: verdict = " AVOID"
        if op['btc_penalty']: verdict = " BTC RISK" # Veredito específico para correlação
        
        obi_str = f"{op['obi']:+.2f}"
        
        # Formatação
        print(f"{op['symbol']:<15} | {op['price']:<10.4f} | {op['spread_pct']:<8.4f} | {obi_str:<6} | {op['score']:<6.1f} | {op['safe_qty']:<10.4f} | ${op['max_capacity_usd']:<15.2f} | {verdict:<10}")

    if opportunities:
        best = opportunities[0]
        print(f"\n MELHOR OPORTUNIDADE: {best['symbol']} (Score {best['score']:.1f})")
        if best['btc_penalty']:
            print(f"   ️ ATENÇÃO: Score reduzido devido à correlação contrária com BTC ({btc_sentiment}).")
        print(f"   Capacidade Máxima do Book: ${best['max_capacity_usd']:.2f} (Antes de virar Baleia)")
        print(f"   Alocação Atual ($1000): {best['liq_status']}")

    else:
        print("\n Nenhuma oportunidade válida encontrada.")


if __name__ == "__main__":
    asyncio.run(find_opportunities())
