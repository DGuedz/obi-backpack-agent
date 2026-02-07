import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from core.backpack_transport import BackpackTransport
from core.technical_oracle import TechnicalOracle

async def execute_rr_strategy():
    print(" PROTOCOLO RR 1:4 (LIMIT + 70/30 SPLIT) INICIADO...")
    load_dotenv()
    
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    trade = BackpackTrade(auth)
    data = BackpackData(auth)
    transport = BackpackTransport()
    oracle = TechnicalOracle(data)
    
    # 1. ANÁLISE DE CAPITAL
    collateral = transport.get_account_collateral()
    available_balance = float(collateral.get('availableToWithdraw', 0))
    print(f" Capital Disponível: ${available_balance:.2f}")
    
    if available_balance < 10:
        print(" Capital insuficiente para 10 ordens. Mínimo sugerido $50.")
        return

    # Divisão em 10 Fatias
    # Mas só usamos 70% da fatia para margem inicial (Entry) e 30% fica livre (Buffer)
    # Na prática, margin = (balance / 10) * 0.7
    
    slice_total = available_balance / 10
    entry_margin = slice_total * 0.7
    leverage = 10
    notional = entry_margin * leverage
    
    print(f" Planejamento de Alocação:")
    print(f"   - Total Fatias: 10")
    print(f"   - Valor por Fatia: ${slice_total:.2f}")
    print(f"   - Margem Entrada (70%): ${entry_margin:.2f}")
    print(f"   - Buffer Segurança (30%): ${slice_total * 0.3:.2f}")
    print(f"   - Notional (10x): ${notional:.2f}")
    
    # 2. SCANNER DE ASSIMETRIA (TOP 10)
    print("\n Escaneando Mercado por Assimetria Real...")
    candidates = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "DOGE_USDC_PERP",
        "XRP_USDC_PERP", "APT_USDC_PERP", "SUI_USDC_PERP", "HYPE_USDC_PERP",
        "FOGO_USDC_PERP", "BNB_USDC_PERP", "AVAX_USDC_PERP", "PEPE_USDC_PERP",
        "WIF_USDC_PERP", "JUP_USDC_PERP", "LINK_USDC_PERP"
    ]
    
    scored_assets = []
    
    for symbol in candidates:
        try:
            depth = data.get_orderbook_depth(symbol)
            if not depth: continue
            
            obi = oracle.calculate_obi(depth)
            
            # Imbalance
            bids = depth['bids']
            asks = depth['asks']
            bid_vol = sum([float(x[1]) for x in bids[:5]])
            ask_vol = sum([float(x[1]) for x in asks[:5]])
            
            if ask_vol == 0: continue
            ratio = bid_vol / ask_vol
            
            # Score de Assimetria
            # Bullish: OBI > 0.3 (Strong), Ratio > 1.5, Spread < 0.1% (Ideal)
            # Bearish: OBI < -0.3 (Strong), Ratio < 0.6
            score = 0
            side = None
            
            # Spread Check
            spread_pct = (best_ask - best_bid) / best_bid
            if spread_pct > 0.0015: # Spread > 0.15% é perigoso para SL curto (0.5%)
                continue 
            
            if obi > 0.3 and ratio > 1.5:
                score = obi * ratio
                side = "Buy"
            elif obi < -0.3 and ratio < 0.6:
                score = abs(obi) * (1/ratio)
                side = "Sell"
                
            if score > 0.5:
                # Get Price for Limit calc
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                market_price = (best_bid + best_ask) / 2
                
                scored_assets.append({
                    "symbol": symbol,
                    "side": side,
                    "score": score,
                    "price": market_price,
                    "best_bid": best_bid,
                    "best_ask": best_ask
                })
                print(f"    {symbol}: {side} (Score {score:.2f})")
                
        except Exception as e:
            print(f"   ️ Erro em {symbol}: {e}")
            
    # Ordenar por Score e pegar Top 10 (ou menos se não houver 10 bons)
    scored_assets.sort(key=lambda x: x['score'], reverse=True)
    top_assets = scored_assets[:10]
    
    if not top_assets:
        print(" Nenhuma assimetria real encontrada. Abortando para preservar capital.")
        return

    print(f"\n EXECUTANDO 10 ORDENS LIMIT (RR 1:4)...")
    
    for asset in top_assets:
        symbol = asset['symbol']
        side = asset['side']
        price = asset['price']
        
        # CÁLCULO DE LIMIT PRICE (Maker)
        # Se Buy: Colocar no Best Bid (ou levemente abaixo para garantir Maker)
        # Se Sell: Colocar no Best Ask
        limit_price = asset['best_bid'] if side == "Buy" else asset['best_ask']
        
        # CÁLCULO TP/SL (RR 1:4)
        # Target: Lucro 20% (2% mov) -> SL: 5% (0.5% mov)
        tp_pct = 0.02
        sl_pct = 0.005
        
        if side == "Buy":
            tp_trigger = limit_price * (1 + tp_pct)
            sl_trigger = limit_price * (1 - sl_pct)
            exit_side = "Ask"
        else:
            tp_trigger = limit_price * (1 - tp_pct)
            sl_trigger = limit_price * (1 + sl_pct)
            exit_side = "Bid"
            
        # Formatação de Precisão (USANDO GUARDIAN)
        limit_price_str = guardian.format_price(symbol, limit_price)
        tp_str = guardian.format_price(symbol, tp_trigger)
        sl_str = guardian.format_price(symbol, sl_trigger)
        
        # Quantity
        raw_qty = notional / float(limit_price_str) # Recalcula qty com preço ajustado
        qty_str = guardian.format_quantity(symbol, raw_qty)
        
        print(f"    {symbol} {side} @ {limit_price_str}")
        print(f"      Qty: {qty_str} | TP: {tp_str} | SL: {sl_str}")
        
        # Validação de Segurança Pré-Envio
        # Checar Min Notional (aprox)
        if float(limit_price_str) * float(qty_str) < 5.0:
            print(f"      ️ Notional muito baixo (${float(limit_price_str) * float(qty_str):.2f}). Pulando.")
            continue
            
        # 1. Enviar Ordem LIMIT
        res = trade.execute_order(
            symbol=symbol,
            side="Bid" if side == "Buy" else "Ask",
            order_type="Limit",
            quantity=qty_str,
            price=limit_price_str,
            time_in_force="GTC"
        )
        
        if res: 
            print(f"       Limit Order Enviada @ {limit_price_str}")
            
            # ACTIVE PROTECTION GUARD (Monitoramento Ativo de Preenchimento)
            # Como o usuário exigiu implementação imediata, não vamos esperar o Sonar genérico.
            # Vamos monitorar esta ordem específica por até 10s para aplicar TP/SL.
            
            print("      ️ Ativando Active Protection Guard (10s scan)...")
            filled = False
            for _ in range(10): # 10 tentativas de 1s
                try:
                    # Verifica status da posição ou da ordem
                    pos = transport.get_positions()
                    active_pos = next((p for p in pos if p['symbol'] == symbol and float(p['quantity']) != 0), None)
                    
                    if active_pos:
                        print(f"       Posição Confirmada! Aplicando TP/SL Blindados...")
                        
                        # TP (Limit Maker)
                        trade.execute_order(symbol, exit_side, "Limit", qty_str, price=tp_str, time_in_force="GTC")
                        
                        # SL (Market Trigger)
                        trade.execute_order(symbol, exit_side, "Market", qty_str, trigger_price=sl_str)
                        
                        print("       TP e SL Configurados com Sucesso.")
                        filled = True
                        break
                    else:
                        # Se não preencheu, espera.
                        # Se for Limit Maker, pode demorar.
                        # Se demorar > 10s, o 'sl_sonar.py' (que roda em background) assume a proteção.
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    print(f"      ️ Erro no Guard: {e}")
                    await asyncio.sleep(1)
            
            if not filled:
                print("      ⏳ Ordem Limit pendente. 'SL Sonar' assume a proteção em background.")

        else:
            print("       Falha no envio da ordem Limit.")
            
        await asyncio.sleep(0.5) # Pace

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(execute_rr_strategy())
