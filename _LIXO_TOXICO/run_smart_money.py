import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from smart_money_engine import SmartMoneyEngine

load_dotenv()

def scan_smart_money_opportunities():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    engine = SmartMoneyEngine(data, trade)

    print(" INICIANDO SCAN INSTITUCIONAL (SMART MONEY)...")
    print("=" * 60)

    # 1. Selecionar Top Markets (Volume)
    tickers = data.get_tickers()
    perp_tickers = [t for t in tickers if 'PERP' in t['symbol']]
    perp_tickers.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
    top_markets = perp_tickers[:10] # Top 10 liquidez

    for m in top_markets:
        symbol = m['symbol']
        price = float(m['lastPrice'])
        
        # 2. Detectar Liquidity Walls
        bid_walls, ask_walls = engine.detect_liquidity_walls(symbol)
        
        has_walls = not bid_walls.empty or not ask_walls.empty
        
        # 3. Detectar SFP (Swing Failure Pattern)
        sfp_status = engine.detect_sfp(symbol, timeframe="15m")
        
        # 4. VSA Check
        vsa_valid, vol, avg_vol = engine.validate_vsa_breakout(symbol, timeframe="15m")
        
        # Logica de Sinal
        signal = None
        reason = []
        
        if sfp_status == "BULLISH_SFP":
            signal = "LONG (SFP)"
            reason.append("Liquidity Grab (Low) + Rejection")
            if not bid_walls.empty:
                # Se tem parede de compra logo abaixo, reforça
                reason.append(f"Bid Wall Support @ {bid_walls.iloc[0]['price']}")
                
        elif sfp_status == "BEARISH_SFP":
            signal = "SHORT (SFP)"
            reason.append("Liquidity Grab (High) + Rejection")
            if not ask_walls.empty:
                reason.append(f"Ask Wall Resistance @ {ask_walls.iloc[0]['price']}")

        # Filtro VSA
        if signal and not vsa_valid:
            signal += " [WEAK VOLUME]"
            reason.append(f"Vol {vol:.0f} < 2x SMA {avg_vol:.0f} (Possível Indução)")
        elif signal and vsa_valid:
             signal += " [INSTITUTIONAL VOL]"
             reason.append("High Volume Rejection (Smart Money Footprint)")

        # Print apenas se tiver algo interessante
        if signal or has_walls:
            print(f"\n {symbol} (${price})")
            
            if not bid_walls.empty:
                print(f"    Bid Walls (Suporte Inst.): {bid_walls['price'].tolist()[:3]}")
            if not ask_walls.empty:
                print(f"    Ask Walls (Resistência Inst.): {ask_walls['price'].tolist()[:3]}")
                
            if signal:
                print(f"    SINAL DETECTADO: {signal}")
                for r in reason:
                    print(f"      - {r}")
                print(f"       Ação: Usar Limit Order (PostOnly) na retração.")

    print("\n" + "=" * 60)
    print(" Scan Finalizado. O Agente está observando os rastros do Composite Man.")

if __name__ == "__main__":
    import os
    scan_smart_money_opportunities()
