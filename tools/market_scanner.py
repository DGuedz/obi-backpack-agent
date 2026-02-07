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
from tools.vsc_transformer import VSCLayer

async def scan_market():
    load_dotenv()
    
    # Inicializar
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    # Inicializar Camada VSC (Safe-Mode)
    vsc_layer = VSCLayer()
    
    targets = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", 
        "HYPE_USDC_PERP", "MON_USDC_PERP", "FRAG_USDC_PERP", 
        "JTO_USDC_PERP", "SUI_USDC_PERP", "APT_USDC_PERP",
        "FLOCK_USDC_PERP", "DOGE_USDC_PERP"
    ]
    
    print("\n MARKET SCAN REPORT (THE MENU)")
    print("-" * 65)
    print(f"{'SYMBOL':<15} | {'PRICE':<10} | {'TREND':<10} | {'OBI':<6} | {'PULSE':<8}")
    print("-" * 65)
    
    pulse = oracle.get_market_pulse()
    
    for symbol in targets:
        try:
            # Dados Básicos
            depth = data_client.get_orderbook_depth(symbol)
            
            # [VSC INJECTION] Bufferizar snapshot para Oracle Context
            # Assumindo que depth tem bids/asks, precisamos extrair best_bid/ask para o formato VSC esperado
            if depth and 'bids' in depth and 'asks' in depth:
                best_bid = float(depth['bids'][-1][0]) if depth['bids'] else 0
                best_ask = float(depth['asks'][0][0]) if depth['asks'] else 0
                depth_snapshot = {
                    "symbol": symbol,
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "spread": best_ask - best_bid
                }
                vsc_layer.update_scout_buffer(symbol, depth_snapshot)

            obi = oracle.calculate_obi(depth, detect_spoofing=True)
            
            klines = data_client.get_klines(symbol, "15m", limit=60)
            if not klines: continue
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            current_price = df.iloc[-1]['close']
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            trend = "BULLISH" if current_price > ema_50 else "BEARISH"
            
            # Format
            obi_str = f"{obi:+.2f}"
            trend_icon = "🟢" if trend == "BULLISH" else ""
            
            print(f"{symbol:<15} | {current_price:<10.4f} | {trend_icon} {trend:<7} | {obi_str:<6} | {pulse}")
            
        except Exception as e:
            print(f"{symbol:<15} | ERROR: {e}")
            
    print("-" * 65)
    print(f"️ MARKET PULSE: {pulse}")
    
    # [VSC DEBUG] Mostrar buffer acumulado (demonstração)
    print("\n[VSC LAYER] Buffered Context (Last Snapshot):")
    for sym in targets[:3]: # Show first 3 only
        ctx = vsc_layer.get_market_proxy_context(sym)
        if ctx:
            print(f" > {sym}: {ctx[-1]}")

    print(" Instrução: Use 'python3 tools/manual_entry.py --symbol SYMBOL --side SIDE' para operar.")

if __name__ == "__main__":
    asyncio.run(scan_market())
