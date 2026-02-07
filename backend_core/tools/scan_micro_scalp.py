
import os
import sys
import asyncio
import pandas as pd
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), 'strategies'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.technical_oracle import TechnicalOracle
from tools.vsc_transformer import VSCTransformer

async def scan_market_micro_scalp():
    load_dotenv()
    
    # Inicializar
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    vsc = VSCTransformer()
    
    # Lista Ampliada de Ativos (Focus: High Volatility & Liquidity)
    targets = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
        "HYPE_USDC_PERP", "MON_USDC_PERP", "FRAG_USDC_PERP", 
        "JTO_USDC_PERP", "SUI_USDC_PERP", "APT_USDC_PERP",
        "FLOCK_USDC_PERP", "DOGE_USDC_PERP", "WIF_USDC_PERP",
        "BONK_USDC_PERP", "JUP_USDC_PERP", "RENDER_USDC_PERP",
        "NEAR_USDC_PERP", "TIA_USDC_PERP", "INJ_USDC_PERP",
        "PEPE_USDC_PERP", "PENGU_USDC_PERP", "ZORA_USDC_PERP"
    ]
    
    print("\n MICRO SCALP SCANNER (3x Loop Strategy)")
    print("-" * 80)
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'TREND':<8} | {'VSC':<6} | {'OBI':<6} | {'ACTION':<8}")
    print("-" * 80)
    
    opportunities = []
    
    for symbol in targets:
        try:
            # 1. Fetch Data
            depth = transport.get_orderbook_depth(symbol)
            klines = transport.get_klines(symbol, "5m", limit=50) # Faster TF for Micro Scalp
            
            if not depth or not klines: continue
            
            # 2. Analyze Trend (EMA Cross)
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            current_price = df.iloc[-1]['close']
            ema_9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
            ema_21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
            
            trend = "BULLISH" if ema_9 > ema_21 else "BEARISH"
            trend_icon = "🟢" if trend == "BULLISH" else ""
            
            # 3. VSC & OBI Analysis
            vsc_score, trap, conf = vsc.analyze(depth)
            obi = oracle.calculate_obi(depth)
            
            # 4. Scoring for Micro Scalp
            action = "WAIT"
            score = 0
            
            # Long Logic: Uptrend + Positive VSC + Positive OBI
            if trend == "BULLISH" and vsc_score > 0.3 and obi > 0.1:
                action = "BUY"
                score = vsc_score + obi
            # Short Logic: Downtrend + Negative VSC + Negative OBI
            elif trend == "BEARISH" and vsc_score < -0.3 and obi < -0.1:
                action = "SELL"
                score = abs(vsc_score + obi)
                
            print(f"{symbol:<15} | {current_price:<10.4f} | {trend_icon} {trend:<6} | {vsc_score:+.2f}   | {obi:+.2f}   | {action}")
            
            if action != "WAIT":
                opportunities.append({
                    'symbol': symbol,
                    'side': 'Bid' if action == 'BUY' else 'Ask',
                    'score': score,
                    'price': current_price
                })
            
        except Exception as e:
            # print(f"{symbol:<15} | ERROR: {e}")
            pass
            
    print("-" * 80)
    
    # Return top opportunities
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n TOP MICRO SCALP OPPORTUNITIES:")
    if not opportunities:
        print("    No clear signals found. Market is choppy.")
    else:
        for op in opportunities[:5]:
            print(f"    {op['symbol']} -> {op['side']} (Score: {op['score']:.2f})")

if __name__ == "__main__":
    asyncio.run(scan_market_micro_scalp())
