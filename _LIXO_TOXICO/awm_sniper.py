import os
import time
import requests
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from market_intelligence import MarketIntelligence

load_dotenv()

class AWMSniper:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.mi = MarketIntelligence()
        self.armed = False # Safety Switch
        
        # Config AWM (High Caliber)
        self.leverage = 10
        self.capital = 100 # $100 Shot
        self.sl_pct = 0.015 # 1.5% Stop (Tight)
        self.tp_pct = 0.05 # 5% Target (Explosive)

    def calibrate_scope(self):
        print(" AWM SNIPER: CALIBRANDO MIRA (Latência Zero)...")
        # Check Latency
        start = time.time()
        # Use get_ticker as ping (get_time might not exist in this wrapper version)
        self.data.get_ticker("SOL_USDC_PERP")
        latency = (time.time() - start) * 1000
        print(f"    Latência de Rede: {latency:.1f}ms")
        
        if latency > 500:
            print("   ️ ALERTA: Latência alta. O tiro pode atrasar.")
        else:
            print("    CONEXÃO ESTÁVEL. PRONTO PARA O DISPARO.")

    def scan_and_shoot(self):
        print("\n VARREDURA DE ALVOS (VOLATILIDADE > 17%)...")
        
        # 1. Filtro de Alta Volatilidade
        tickers = self.data.get_tickers()
        candidates = []
        
        for t in tickers:
            if 'PERP' not in t['symbol']: continue
            if float(t.get('quoteVolume', 0)) < 5_000_000: continue # Liquidez Mínima
            
            # Volatilidade Estimada (High/Low)
            high = float(t['high'])
            low = float(t['low'])
            if low == 0: continue
            volatility = (high - low) / low
            
            if volatility > 0.10: # > 10% (Filtro base para achar os 17%)
                candidates.append((t['symbol'], volatility))
        
        # Sort by Volatility
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        print(f"    {len(candidates)} Alvos Potenciais (Vol > 10%)")
        
        for symbol, vol in candidates[:5]:
            print(f"   >> Rastreando {symbol} (Vol: {vol*100:.1f}%)")
            self.check_trigger(symbol)

    def check_trigger(self, symbol):
        # Leitura Rápida de Klines (15m)
        klines = self.data.get_klines(symbol, "15m", limit=30)
        if not klines: return
        
        closes = [float(k['close']) for k in klines]
        volumes = [float(k['volume']) for k in klines]
        price = closes[-1]
        
        # Indicadores
        rsi = self.mi.calculate_rsi(closes)
        bb_upper, bb_mid, bb_lower = self.mi.calculate_bollinger_bands(closes)
        
        # Lógica do AWM (Rompimento Explosivo)
        signal = None
        
        # LONG: Rompeu BB Inferior + RSI Oversold (Reversão em V)
        if price < bb_lower and rsi < 25:
             signal = "LONG (V-REVERSAL)"
             side = "Bid"
             
        # SHORT: Rompeu BB Superior + RSI Overbought (Blow-off Top)
        elif price > bb_upper and rsi > 75:
             signal = "SHORT (BLOW-OFF)"
             side = "Ask"
             
        if signal:
            print(f"    ALVO TRAVADO: {symbol} | {signal}")
            print(f"      RSI: {rsi:.1f} | Preço: {price}")
            
            if self.armed:
                self.take_shot(symbol, side, price)
            else:
                print("       GATILHO BLOQUEADO (Modo Segurança). Ative 'ARMED=True' para disparar.")

    def take_shot(self, symbol, side, price):
        print(f"    PULLING TRIGGER (MARKET ORDER) on {symbol}...")
        
        qty = (self.capital * self.leverage) / price
        
        # Rounding
        if "PEPE" in symbol or "BONK" in symbol or "FOGO" in symbol: qty = int(qty)
        elif price > 1000: qty = round(qty, 3)
        else: qty = round(qty, 1)
        
        try:
            # FIRE! (Market Order for Speed)
            order = self.trade.execute_order(
                symbol=symbol,
                side=side,
                order_type="Market",
                quantity=str(qty)
            )
            print(f"    TIRO CONFIRMADO: ID {order.get('id')}")
            
            # Immediate Protection (Reload)
            self.deploy_shield(symbol, side, price, qty)
            
        except Exception as e:
            print(f"    FALHA NO DISPARO: {e}")

    def deploy_shield(self, symbol, side, entry_price, qty):
        print("   ️ IMPLANTANDO ESCUDO (SL/TP)...")
        # SL Logic
        sl_price = entry_price * (1 - self.sl_pct) if side == "Bid" else entry_price * (1 + self.sl_pct)
        tp_price = entry_price * (1 + self.tp_pct) if side == "Bid" else entry_price * (1 - self.tp_pct)
        
        exit_side = "Ask" if side == "Bid" else "Bid"
        
        # Rounding
        if entry_price > 1000:
            sl_price = round(sl_price, 2)
            tp_price = round(tp_price, 2)
        else:
            sl_price = round(sl_price, 4)
            tp_price = round(tp_price, 4)

        try:
            # SL (Stop Market)
            self.trade.execute_order(
                symbol=symbol,
                side=exit_side,
                order_type="Market",
                quantity=str(qty),
                trigger_price=str(sl_price)
            )
            # TP (Limit)
            self.trade.execute_order(
                symbol=symbol,
                side=exit_side,
                order_type="Limit",
                quantity=str(qty),
                price=str(tp_price)
            )
            print("    ESCUDO ATIVO.")
        except Exception as e:
            print(f"   ️ ERRO NO ESCUDO: {e}")

if __name__ == "__main__":
    sniper = AWMSniper()
    sniper.calibrate_scope()
    
    # Loop de Monitoramento
    while True:
        try:
            sniper.scan_and_shoot()
            print("   ... Recarregando (10s) ...")
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n Sniper AWM Desativado.")
            break
        except Exception as e:
            print(f"️ Erro de Sistema: {e}")
            time.sleep(5)
