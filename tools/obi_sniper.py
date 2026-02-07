import os
import sys
import time
import threading
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../core')))

from core.backpack_transport import BackpackTransport

# CONFIG
MAX_NEGOTIATIONS = 5       # Max simultaneous assets negotiating
NEGOTIATION_TIMEOUT = 30   # Seconds before giving up on an order
CHASE_INTERVAL = 2.0       # Seconds between price checks
MARGIN_PER_TRADE = 3.0     # USD Margin
LEVERAGE = 50              # High Leverage for Sniper
MIN_ROI_TP = 0.05          # 5% ROE Target
MAX_LOSS_ROI = -0.20       # 20% ROE Stop (Tight)

class ObiNegotiator:
    def __init__(self):
        # self.transport = transport # Removed shared transport
        self.active_negotiations = {} # symbol -> thread
        self.lock = threading.Lock()
        self.market_meta = {} # Cache for tick_size, step_size

    def update_market_meta(self, transport):
        try:
            markets = transport._send_request("GET", "/api/v1/markets", "marketsQuery")
            if markets:
                for m in markets:
                    sym = m['symbol']
                    # Backpack filters are usually in 'filters' -> 'price' -> 'tickSize'
                    # Check structure
                    tick_size = 0.01 # Default fallback
                    step_size = 1.0
                    
                    filters = m.get('filters', {})
                    if 'price' in filters:
                        tick_size = float(filters['price'].get('tickSize', 0.01))
                    if 'quantity' in filters:
                        step_size = float(filters['quantity'].get('stepSize', 1.0))
                        
                    self.market_meta[sym] = {
                        'tick_size': tick_size,
                        'step_size': step_size
                    }
                print(f"   ℹ️ [NEGOTIATOR] Meta cache updated for {len(self.market_meta)} markets.")
        except Exception as e:
            print(f"   ️ [NEGOTIATOR] Failed to update market meta: {e}")

    def get_tick_size(self, symbol):
        if symbol in self.market_meta:
            return self.market_meta[symbol]['tick_size']
        return 0.0 # Unknown, be safe

    def get_best_price(self, transport, symbol, side):
        try:
            # Use Depth (Orderbook) for precision
            depth = transport.get_orderbook_depth(symbol, limit=100)
            if not depth:
                print(f"   ️ [DEBUG] {symbol}: Depth retornou vazio.")
                return None
            
            # depth['bids'] -> [['price', 'qty'], ...]
            best_bid = float(depth['bids'][0][0]) if depth.get('bids') else 0.0
            best_ask = float(depth['asks'][0][0]) if depth.get('asks') else 0.0
            
            if best_bid == 0 or best_ask == 0: return None
            
            tick_size = self.get_tick_size(symbol)
            if tick_size == 0:
                # Fallback: infer from spread if possible or assume very small
                tick_size = 0.0001 
            
            # FRONT RUN LOGIC (Antecipação)
            if side == "Buy":
                # Queremos pagar um tick ACIMA do best bid atual
                target = best_bid + tick_size
                # Mas não podemos cruzar o spread (Taker)
                if target >= best_ask:
                    target = best_bid # Se spread for 1 tick, mantemos best bid (join)
                return target
            else:
                # Queremos vender um tick ABAIXO do best ask atual
                target = best_ask - tick_size
                if target <= best_bid:
                    target = best_ask # Se spread for 1 tick, mantemos best ask (join)
                return target

        except Exception as e:
            print(f"   ️ [DEBUG] {symbol}: Exception em get_best_price: {e}")
            return None

    def format_qty(self, symbol, qty, price):
        # Dynamic precision
        if price > 50000: return f"{qty:.5f}" # BTC
        if price > 1000: return f"{qty:.2f}"  # ETH
        if price > 10: return f"{qty:.1f}"    # SOL, AVAX
        return f"{qty:.0f}"                   # MEMEs

    def negotiate(self, symbol, side):
        print(f" [NEGOTIATOR] Iniciando negociação em {symbol} ({side})...")
        
        # Dedicated Transport per Thread (Thread-Safety)
        transport = BackpackTransport()
        
        start_time = time.time()
        order_id = None
        current_price = 0.0
        
        try:
            # 1. Initial Size Calculation
            ticker = transport._send_request("GET", f"/api/v1/ticker?symbol={symbol}", "tickerQuery")
            if not ticker:
                print(f"    [NEGOTIATOR] {symbol}: Falha ao obter ticker inicial.")
                return
            
            price_snap = float(ticker['lastPrice'])
            
            notional = MARGIN_PER_TRADE * LEVERAGE
            raw_qty = notional / price_snap
            qty_str = self.format_qty(symbol, raw_qty, price_snap)
            
            print(f"   ℹ️ [NEGOTIATOR] {symbol}: Size calc: {qty_str} (Price: {price_snap})")
            
            # Negotiation Loop
            while time.time() - start_time < NEGOTIATION_TIMEOUT:
                # A. Get Best Price (The "Counter" Price)
                target_price = self.get_best_price(transport, symbol, side)
                if not target_price:
                    print(f"   ️ [NEGOTIATOR] {symbol}: Sem preço alvo.")
                    time.sleep(1)
                    continue
                
                # B. Check if we need to update
                # If we have an order, check if it's still top of book
                if order_id:
                    # Check status
                    # TODO: Use WebSocket or efficient polling. For now, poll.
                    orders = transport.get_open_orders(symbol)
                    if orders is None:
                        print(f"   ️ [NEGOTIATOR] {symbol}: Erro ao buscar ordens abertas.")
                        time.sleep(1)
                        continue
                        
                    my_order = next((o for o in orders if o['id'] == order_id), None)
                    
                    if not my_order:
                        # Filled or Cancelled externally
                        # Check fill history? Or assume fill if missing and no error?
                        # Let's assume Success for now and verify position later.
                        print(f" [NEGOTIATOR] {symbol}: Oferta ACEITA! (Ordem preenchida ou sumiu)")
                        return
                    
                    # If open, check price drift
                    my_price = float(my_order['price'])
                    
                    # If Buying: target_price (Best Bid) > my_price => We are outbid. Chase UP.
                    # If Selling: target_price (Best Ask) < my_price => We are undercut. Chase DOWN.
                    drift = False
                    if side == "Buy" and target_price > my_price: drift = True
                    if side == "Sell" and target_price < my_price: drift = True
                    
                    if drift:
                        print(f"    [NEGOTIATOR] {symbol}: Recusaram ${my_price}. Melhorando para ${target_price}...")
                        transport.cancel_order(symbol, order_id)
                        order_id = None # Ready to place new
                    else:
                        # We are still best, wait.
                        # print(f"   ⏳ [NEGOTIATOR] {symbol}: Aguardando... (Minha oferta: ${my_price} é Topo)")
                        time.sleep(CHASE_INTERVAL)
                        continue
                
                # C. Place Order (If none active)
                if not order_id:
                    # Place Post-Only Limit
                    payload = {
                        "symbol": symbol,
                        "side": side,
                        "orderType": "Limit",
                        "quantity": qty_str,
                        "price": str(target_price),
                        "postOnly": True
                    }
                    print(f"    [NEGOTIATOR] {symbol}: Enviando oferta: ${target_price}...")
                    res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
                    
                    if res and 'id' in res:
                        order_id = res['id']
                        current_price = target_price
                        print(f"    [NEGOTIATOR] {symbol}: Oferta na mesa: ${target_price}")
                    else:
                        # Post Only rejected? Means we crossed. Retry with adjusted price next loop.
                        # Or maybe just wait.
                        print(f"    [NEGOTIATOR] {symbol}: Oferta rejeitada: {res}")
                        time.sleep(1)
                        
                time.sleep(CHASE_INTERVAL)
                
            # Timeout
            if order_id:
                print(f"   ⏱️ [NEGOTIATOR] {symbol}: Tempo esgotado. Cancelando oferta final.")
                transport.cancel_order(symbol, order_id)
                
        except Exception as e:
            print(f"    [NEGOTIATOR] Erro em {symbol}: {e}")
        finally:
            with self.lock:
                if symbol in self.active_negotiations:
                    del self.active_negotiations[symbol]

    def start_negotiation(self, symbol, side):
        with self.lock:
            if symbol in self.active_negotiations:
                return # Already negotiating
            if len(self.active_negotiations) >= MAX_NEGOTIATIONS:
                return # Full capacity
            
            t = threading.Thread(target=self.negotiate, args=(symbol, side))
            self.active_negotiations[symbol] = t
            t.start()


def scan_and_snipe():
    print(" OBI SNIPER: SCANNING & NEGOTIATING...")
    # transport = BackpackTransport() # Removed global
    negotiator = ObiNegotiator() # No transport passed
    
    # Initial Meta Update
    print("   ℹ️ Updating Market Metadata...")
    meta_transport = BackpackTransport()
    negotiator.update_market_meta(meta_transport)
    
    while True:
        try:
            # 1. Scan Market (Simple Volatility Logic for now)
            # Use a fresh transport for scanning
            scanner_transport = BackpackTransport()
            tickers = scanner_transport._send_request("GET", "/api/v1/tickers", "tickerQuery")
            if not tickers: 
                time.sleep(5)
                continue
                
            perps = [t for t in tickers if 'PERP' in t['symbol'] and 'USDC' in t['symbol']]
            
            # Filter Volatile Assets (Opportunities)
            # Sort by absolute change
            opportunities = sorted(perps, key=lambda x: abs(float(x.get('priceChangePercent', 0))), reverse=True)
            
            # SWEEP: Aumentar cobertura para Top 20 e filtrar Volume > 0
            # Evitar ativos mortos
            valid_opps = []
            for t in opportunities:
                if float(t.get('quoteVolume', 0)) > 100000: # Min $100k volume
                    valid_opps.append(t)
            
            for opp in valid_opps[:20]: # Top 20 Volatile
                symbol = opp['symbol']
                change = float(opp.get('priceChangePercent', 0))
                
                # Logic: Trend Follow? Or Mean Reversion?
                # User says "melhores entradas". 
                # Let's go with Trend Following for Sniper logic (catch the run).
                side = "Buy" if change > 0 else "Sell"
                
                # Check if we already have a position?
                # For now, Negotiator handles concurrency limit.
                
                negotiator.start_negotiation(symbol, side)
                
            time.sleep(5) # Scan interval
            
        except KeyboardInterrupt:
            print("\n Stopping Obi Sniper...")
            break
        except Exception as e:
            print(f" Main Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    scan_and_snipe()
