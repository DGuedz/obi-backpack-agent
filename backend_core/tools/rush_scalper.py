import os
import sys
import time
import requests
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'core')))

from backpack_transport import BackpackTransport

def rush_scalper():
    print(" RUSH SCALPER: LETHAL PRECISION MODE (LOOP)")
    print("="*60)
    print(" Setup: Recarregar, Atirar, Evadir.")
    print(" Loop Infinito: Ctrl+C para parar.")
    
    load_dotenv()
    transport = BackpackTransport()
    
    # Configuration
    MIN_PROFIT_TO_EVADE = 0.20  # Close if profit > $0.20
    STOP_LOSS_THRESHOLD = -1.50 # Close if loss > $1.50 (Hard Stop)
    MAX_POSITIONS = 3
    MIN_EQUITY_TO_ENGAGE = 1.0  # Minimum equity to start a new trade
    
    while True:
        try:
            print("\n" + "-"*30)
            print(f"⏰ {time.strftime('%H:%M:%S')} - Scanning Battlefield...")
            
            # 1. Check Active Position (Enemy Contact)
            positions = transport._send_request("GET", "/api/v1/position", "positionQuery")
            active_symbols = []
            
            if positions:
                print(f"️  Inimigo em Combate! {len(positions)} posições ativas.")
                for p in positions:
                    sym = p.get('symbol')
                    active_symbols.append(sym)
                    pnl = float(p.get('unrealizedPnl', 0))
                    entry = float(p.get('entryPrice', 0))
                    mark = float(p.get('markPrice', 0))
                    side = p.get('side')
                    qty_p = float(p.get('quantity', 0))
                    
                    print(f"   ️ {sym} ({side}): PnL ${pnl:.4f} | Entry: {entry} | Mark: {mark}")
                    
                    # EVADE LOGIC (Take Profit)
                    if pnl > MIN_PROFIT_TO_EVADE:
                         print(f"    ALVO NEUTRALIZADO! Lucro ${pnl:.4f}. Evadindo...")
                         close_side = "Bid" if side == "Short" else "Ask"
                         # Format quantity string carefully
                         qty_str = str(abs(qty_p))
                         
                         payload = {"symbol": sym, "side": close_side, "orderType": "Market", "quantity": qty_str}
                         res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
                         print(f"       Evadido: {res}")
                         time.sleep(1)
                         
                    # STOP LOSS LOGIC
                    elif pnl < STOP_LOSS_THRESHOLD:
                         print(f"    DANO CRÍTICO! PnL ${pnl:.4f}. Abortando missão neste ativo.")
                         close_side = "Bid" if side == "Short" else "Ask"
                         qty_str = str(abs(qty_p))
                         payload = {"symbol": sym, "side": close_side, "orderType": "Market", "quantity": qty_str}
                         res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
                         print(f"      ️ Abortado: {res}")
                         time.sleep(1)
            else:
                print(" Área Limpa (Sem posições ativas).")

            # 2. Check Ammo (Capital)
            collateral = transport._send_request("GET", "/api/v1/capital/collateral", "collateralQuery")
            equity = float(collateral.get('netEquityAvailable', 0))
            print(f"� Munição Disponível: ${equity:.2f}")
            
            # If we have max positions, don't shoot more
            if len(active_symbols) >= MAX_POSITIONS:
                print(" Máximo de posições atingido. Monitorando...")
                time.sleep(5)
                continue

            if equity < MIN_EQUITY_TO_ENGAGE:
                print(f"️ Munição Baixa (< ${MIN_EQUITY_TO_ENGAGE}). Aguardando recuperação ou recarga...")
                time.sleep(5)
                continue

            # 3. Select Targets (Scan High Volatility from VIP LIST)
            print(" Buscando Alvos Prioritários (VIP SQUAD)...")
            tickers = transport._send_request("GET", "/api/v1/tickers", "tickerQuery")
            
            # VIP List (High Leverage Supported)
            vip_symbols = [
                'BTC_USDC_PERP', 'ETH_USDC_PERP', 'SOL_USDC_PERP', 
                'HYPE_USDC_PERP', 'XRP_USDC_PERP', 'DOGE_USDC_PERP',
                'WIF_USDC_PERP', 'PEPE_USDC_PERP', 'SUI_USDC_PERP'
            ]
            
            perps = [t for t in tickers if t['symbol'] in vip_symbols]
            
            # Sort by absolute volatility (change) to find the hottest targets
            # But we also want to avoid already active symbols
            targets = []
            for t in perps:
                if t['symbol'] in active_symbols: continue
                targets.append(t)
                
            sorted_targets = sorted(targets, key=lambda x: abs(float(x.get('priceChangePercent', 0))), reverse=True)
            
            if not sorted_targets:
                print("    Nenhum alvo disponível.")
                time.sleep(5)
                continue
                
            # Pick the single best target to concentrate fire
            target = sorted_targets[0]
            sym = target['symbol']
            change = float(target.get('priceChangePercent', 0))
            price = float(target['lastPrice'])
            
            print(f"    Alvo Selecionado: {sym} (Vol: {change:.2f}%) @ ${price}")
            
            # Determine Strategy (Follow the trend)
            side = "Buy" if change > 0 else "Sell" 
            
            # Calculate Ammo Size (Dynamic)
            # Use up to $5, or whatever is available if less
            margin_usd = min(5.0, equity * 0.95)
            
            # Leverage Rules
            leverage = 20
            if "BTC" in sym or "ETH" in sym or "SOL" in sym:
                leverage = 50
            
            notional = margin_usd * leverage
            qty = notional / price
            
            # Precision Adjust (Custom per VIP Asset)
            if "BTC" in sym: qty_str = f"{qty:.5f}"
            elif "ETH" in sym: qty_str = f"{qty:.2f}"
            elif "SOL" in sym: qty_str = f"{qty:.2f}"
            elif "HYPE" in sym: qty_str = f"{qty:.1f}"
            elif "XRP" in sym or "SUI" in sym: qty_str = f"{qty:.0f}"
            elif "DOGE" in sym: qty_str = f"{qty:.0f}"
            elif "PEPE" in sym or "WIF" in sym: qty_str = f"{qty:.0f}"
            else: qty_str = f"{qty:.1f}"
            
            # Fix Side
            api_side = "Bid" if side == "Buy" else "Ask"
            
            payload = {
                "symbol": sym,
                "side": api_side,
                "orderType": "Market",
                "quantity": qty_str
            }
            
            print(f"       Disparando {api_side} {qty_str} (Lev: {leverage}x, Margin: ${margin_usd:.2f})...")
            res = transport._send_request("POST", "/api/v1/order", "orderExecute", payload)
            
            if res and 'id' in str(res): 
                 print(f"       IMPACTO CONFIRMADO! Order ID: {res}")
            else:
                 print(f"       FALHA NO DISPARO: {res}")
            
            # Wait a bit before next loop to avoid spamming too hard
            time.sleep(3)
            
        except Exception as e:
            print(f" Erro Crítico no Loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    rush_scalper()
