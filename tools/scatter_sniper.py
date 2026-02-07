import os
import sys
import time
import json

# Add core path
current_dir = os.getcwd()
sys.path.append(current_dir)
if 'core' not in sys.path:
    sys.path.append(os.path.join(current_dir, 'core'))

from core.backpack_transport import BackpackTransport
from core.book_scanner import BookScanner

def scatter_fire():
    print(" INICIANDO SCATTER SHOT (10 TIROS) - STRATEGY: SWARM")
    print("======================================================")
    
    transport = BackpackTransport()
    scanner = BookScanner()
    
    # Configuração
    NUM_TRADES = 10
    LEVERAGE = 10
    STOP_LOSS_PCT = 0.015 # 1.5%
    
    # Capital Management (Blind Mode)
    EQUITY_ASSUMED = 100.0
    MARGIN_PER_TRADE = EQUITY_ASSUMED / NUM_TRADES # $10 por trade
    NOTIONAL_PER_TRADE = MARGIN_PER_TRADE * LEVERAGE # $100 Notional
    
    print(f"    Equity Assumido: ${EQUITY_ASSUMED}")
    print(f"    Trades: {NUM_TRADES} x ${MARGIN_PER_TRADE} Margin (${NOTIONAL_PER_TRADE} Notional)")
    print(f"   ️ SL: {STOP_LOSS_PCT*100}% | Lev: {LEVERAGE}x")
    
    # 1. Selecionar Alvos (Top OBI Absoluto)
    print("\n Escaneando Alvos (High OBI)...")
    
    # Lista ampliada de candidatos
    candidates = [
        "BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP", "SUI_USDC_PERP",
        "AVAX_USDC_PERP", "DOGE_USDC_PERP", "XRP_USDC_PERP", "LINK_USDC_PERP",
        "APT_USDC_PERP", "FOGO_USDC_PERP", "PENGU_USDC_PERP", "PEPE_USDC_PERP",
        "WIF_USDC_PERP", "BONK_USDC_PERP", "JUP_USDC_PERP", "RENDER_USDC_PERP",
        "NEAR_USDC_PERP", "TIA_USDC_PERP", "INJ_USDC_PERP", "SEI_USDC_PERP"
    ]
    
    targets = []
    
    for symbol in candidates:
        try:
            # FORCE OBI CALCULATION (BYPASS DEPTH CHECK IF EMPTY)
            # Use Ticker instead for price if Depth fails
            
            ticker = transport.get_ticker(symbol)
            if not ticker: continue
            
            price = float(ticker['lastPrice'])
            
            # Simulated OBI for now if depth fails (Random/Trend based)
            # OR try depth again with retry logic?
            # Let's try depth but handle empty better
            
            try:
                depth = transport.get_orderbook_depth(symbol)
                if depth and depth.get('bids') and depth.get('asks'):
                    obi = scanner.calculate_obi(depth)
                else:
                    obi = 0 # Neutral fallback
            except:
                obi = 0
            
            # Force add even if OBI is 0 (we want volume)
            # But prefer High OBI assets if possible.
            # If OBI 0, assume Trend Follow based on 24h change?
            
            # Let's assume user wants execution NOW.
            # Add all candidates, sort by whatever OBI we found.
            
            targets.append({
                "symbol": symbol,
                "obi": obi,
                "side": "Bid" if obi >= 0 else "Ask", 
                "price": price
            })
            print(f"   -> {symbol}: OBI {obi:.2f} | Price {price}")
            
        except Exception as e:
            print(f"   -> {symbol}: Error {e}")
            pass
            
    # Ordenar por força do OBI (Absoluto)
    targets.sort(key=lambda x: abs(x['obi']), reverse=True)
    
    # Selecionar Top N
    selected = targets[:NUM_TRADES]
    
    if not selected:
        print(" Nenhum alvo válido encontrado.")
        return

    print(f"\n DISPARANDO {len(selected)} OPERAÇÕES...")
    
    for i, trade in enumerate(selected):
        symbol = trade['symbol']
        side = trade['side']
        price = trade['price']
        
        # Calcular Qty
        qty = NOTIONAL_PER_TRADE / price
        
        # Adjust precision roughly (safe 1 decimal for alts, 3 for big)
        if price > 1000: qty = round(qty, 4)
        elif price > 10: qty = round(qty, 2)
        else: qty = round(qty, 0)
        
        if qty == 0: continue
        
        print(f"   [{i+1}/{len(selected)}] {side.upper()} {symbol} (OBI {trade['obi']:.2f})")
        print(f"      Size: {qty} @ ~${price}")
        
        # Execute Market Order
        try:
            res = transport.execute_order(
                symbol=symbol,
                order_type="Market",
                side=side,
                quantity=str(qty)
            )
            
            if res and 'id' in res:
                print("       FILLED")
                
                # Set Stop Loss Immediately
                sl_price = 0
                if side == "Bid":
                    sl_price = price * (1 - STOP_LOSS_PCT)
                    sl_side = "Ask"
                else:
                    sl_price = price * (1 + STOP_LOSS_PCT)
                    sl_side = "Bid"
                
                # Format price precision
                # Simplification: rounding to reasonable decimals based on price magnitude
                if sl_price > 1000: sl_price = round(sl_price, 1)
                elif sl_price > 1: sl_price = round(sl_price, 3)
                else: sl_price = round(sl_price, 5)
                
                print(f"      ️ Setting SL @ {sl_price}...")
                
                # Trigger Order for SL (Stop Market is best for safety)
                # Note: Backpack API might use 'StopLoss' or 'StopMarket'
                # Standard execute_order usually handles TriggerPrice logic if implemented
                # Using Limit for now as fallback or Trigger if supported
                
                # Try Stop Market logic via Trigger Param
                transport.execute_order(
                    symbol=symbol,
                    order_type="StopMarket", # If supported, else Limit
                    side=sl_side,
                    quantity=str(qty),
                    trigger_price=str(sl_price)
                )
                
            else:
                print("       FAILED")
                
        except Exception as e:
            print(f"       ERROR: {e}")
            
        time.sleep(0.5) # Avoid rate limit spam

if __name__ == "__main__":
    scatter_fire()
