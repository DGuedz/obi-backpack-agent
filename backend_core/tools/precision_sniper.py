import asyncio
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from core.technical_oracle import TechnicalOracle

async def precision_strike():
    print(" PRECISION SNIPER: INICIANDO VARREDURA TÁTICA...")
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    # Alvos Potenciais
    targets = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP",
        "DOGE_USDC_PERP", "XRP_USDC_PERP", "APT_USDC_PERP",
        "SUI_USDC_PERP", "HYPE_USDC_PERP", "FOGO_USDC_PERP"
    ]
    
    best_asset = None
    best_score = 0
    best_side = None
    best_obi = 0
    
    print(f"\n ANALISANDO LIVRO DE OFERTAS (OBI & IMBALANCE)...")
    print(f"{'ATIVO':<10} | {'OBI':<6} | {'IMBALANCE':<10} | {'VEREDITO'}")
    print("-" * 60)
    
    for symbol in targets:
        try:
            depth = data.get_orderbook_depth(symbol)
            if not depth: continue
            
            obi = oracle.calculate_obi(depth)
            
            # Imbalance Ratio
            bids = depth['bids']
            asks = depth['asks']
            bid_vol = sum([float(x[1]) for x in bids[:5]])
            ask_vol = sum([float(x[1]) for x in asks[:5]])
            ratio = bid_vol / ask_vol if ask_vol > 0 else 0
            
            verdict = "NEUTRO"
            score = 0
            
            # Critérios de Precisão (Bullish)
            if obi > 0.3 and ratio > 1.5:
                verdict = "🟢 COMPRA FORTE"
                score = obi * ratio
                side = "Buy"
            # Critérios de Precisão (Bearish)
            elif obi < -0.3 and ratio < 0.6:
                verdict = " VENDA FORTE"
                score = abs(obi) * (1/ratio if ratio > 0 else 2)
                side = "Sell"
                
            print(f"{symbol:<10} | {obi:>6.2f} | {ratio:>5.2f}x     | {verdict}")
            
            if score > best_score:
                best_score = score
                best_asset = symbol
                best_side = side
                best_obi = obi
                
        except Exception as e:
            print(f"Erro em {symbol}: {e}")
            
    if best_asset and best_score > 0.5:
        print(f"\n MELHOR OPORTUNIDADE IDENTIFICADA: {best_asset}")
        print(f"   Direção: {best_side}")
        print(f"   Força do Sinal (Score): {best_score:.2f}")
        
        # Confirmação do Usuário (Simulada pela diretiva "vamos entrar")
        print("\n EXECUTANDO ENTRADA DE PRECISÃO (10x Leverage)...")
        
        # Parâmetros
        size_usd = 20.0 # Margem
        leverage = 10
        notional = size_usd * leverage
        
        # Preço Atual
        ticker = data.get_ticker(best_asset)
        price = float(ticker['lastPrice'])
        raw_qty = notional / price
        
        # Rounding Heuristic
        if price > 1000: # BTC, ETH
            qty = f"{raw_qty:.3f}"
        elif price > 10: # SOL, AVAX
            qty = f"{raw_qty:.2f}"
        elif price > 1: # SUI, XRP
            qty = f"{raw_qty:.1f}"
        else: # DOGE, HYPE
            qty = f"{int(raw_qty)}"
            
        print(f"   Qty Formatado: {qty}")
        
        # Executar Entrada
        # trade.execute_order(...)
        # Aqui vamos usar o método execute_order do BackpackTrade que já cuida do payload
        
        res = trade.execute_order(
            symbol=best_asset,
            side="Bid" if best_side == "Buy" else "Ask",
            order_type="Market",
            quantity=qty,
            price=None
        )
        
        if res:
            print(f"    ORDEM ENVIADA: {res.get('status', 'SENT')}")
            
            # CONFIGURAR TP/SL BLINDADOS (Protocolo TriggerMarket validado)
            # TP: 1.5% mov (15% ROI)
            # SL: 0.5% mov (5% Risk)
            
            tp_pct = 0.015
            sl_pct = 0.005
            
            if best_side == "Buy":
                raw_tp = price * (1 + tp_pct)
                raw_sl = price * (1 - sl_pct)
                exit_side = "Ask"
            else:
                raw_tp = price * (1 - tp_pct)
                raw_sl = price * (1 + sl_pct)
                exit_side = "Bid"
                
            # Price Rounding Heuristic
            def format_price(p):
                if p > 1000: return f"{p:.1f}"
                elif p > 10: return f"{p:.2f}"
                elif p > 1: return f"{p:.4f}"
                else: return f"{p:.5f}"
                
            tp_price = format_price(raw_tp)
            sl_price = format_price(raw_sl)
                
            # TP
            print(f"    Configurando TP @ {tp_price} (TriggerMarket)...")
            tp_res = trade.execute_order(
                symbol=best_asset,
                side=exit_side,
                order_type="TriggerMarket", # Agora mapeado para Market + triggerPrice
                quantity=qty,
                price=None,
                trigger_price=tp_price
            )
            if tp_res: print("    TP CONFIGURADO.")
            
            # SL
            print(f"   ️ Configurando SL @ {sl_price:.5f} (TriggerMarket)...")
            sl_res = trade.execute_order(
                symbol=best_asset,
                side=exit_side,
                order_type="TriggerMarket", # Agora mapeado
                quantity=qty,
                price=None,
                trigger_price=sl_price
            )
            if sl_res: print("    SL CONFIGURADO.")
        else:
            print("    FALHA NA EXECUÇÃO DA ORDEM PRINCIPAL.")
        
    else:
        print("\n️ Nenhuma oportunidade de ALTA PRECISÃO encontrada no momento.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(precision_strike())
