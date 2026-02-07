import pandas as pd
import numpy as np
import time

class WeaverGrid:
    def __init__(self, symbol, data_engine, trade_engine, indicators):
        self.symbol = symbol
        self.data = data_engine
        self.trade = trade_engine
        self.indicators = indicators
        self.grid_orders = []
        self.SPREAD_THRESHOLD = 0.001 # 0.1%

    def execute_grid(self, spacing_multiplier=1.0, layers=3, sentinel=None):
        """
        Executa a lógica do Weaver Grid Multi-Nível com Smart Sizing e TrendGuard.
        sentinel: Instância do Sentinel para verificação de tendência.
        """
        print(f"️ [WEAVER] Analisando Grid Multi-Nível para {self.symbol}...")
        
        # 0. Trend Guard Check
        if sentinel:
            trend_status = sentinel.check_trend_integrity(self.symbol)
            if trend_status == 'CRASH':
                print(f"    [TREND GUARD] CRASH DETECTED (Price < EMA 200). Long Grid BLOCKED.")
                return # Block execution
            elif trend_status == 'WARNING':
                print(f"   ️ [TREND GUARD] Warning. Reducing Layer Count to 1.")
                layers = 1 # Defensive mode
        
        # 0. Force Leverage
        try:
            self.trade.set_leverage(self.symbol, 10)
        except Exception as e:
            pass
        
        # 1. Fetch Data
        candles = self.data.get_klines(self.symbol, "1h", limit=50)
        if not candles: return

        df = pd.DataFrame(candles)
        df = df.rename(columns={'start': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'})
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        atr = self.indicators.calculate_atr(df, window=14).iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # 2. Check Margin & Sizing
        try:
            collat = self.data.get_account_collateral()
            available_margin = float(collat.get('netEquityAvailable', 0))
        except:
            available_margin = 50.0 # Safe default
            
        print(f"    Available Margin: ${available_margin:.2f}")
        
        # Desired Notional: $2000 per order -> $200 Margin (10x)
        TARGET_NOTIONAL = 2000.0
        REQUIRED_MARGIN = TARGET_NOTIONAL / 10.0
        
        if available_margin < REQUIRED_MARGIN:
            # Scale down to fit margin
            # Use 90% of available to leave room
            safe_margin = available_margin * 0.90
            TARGET_NOTIONAL = safe_margin * 10.0
            print(f"   ️ Margin Tight. Scaling Down Notional to: ${TARGET_NOTIONAL:.2f}")
        else:
            print(f"    Margin Sufficient for Heavy Artillery ($2000 Notional).")
            
        if TARGET_NOTIONAL < 50.0: # Minimum viable trade size ($5)
             print("    Margin too low to trade safely. Aborting Grid.")
             return

        # 3. Base Grid Spacing (Tight for Night Ops)
        base_spacing = (atr * 0.3) * spacing_multiplier
        
        print(f"    ATR (1h): {atr:.4f} | Price: {current_price:.2f}")
        print(f"    Base Spacing: {base_spacing:.4f} | Layers: {layers}")
        
        # Execution Loop (Layers)
        for i in range(1, layers + 1):
            layer_spacing = base_spacing * i
            
            buy_price = current_price - layer_spacing
            sell_price = current_price + layer_spacing
            
            qty = TARGET_NOTIONAL / current_price
            qty = round(qty, 4)
            buy_price = round(buy_price, 1)
            sell_price = round(sell_price, 1)
            
            print(f"   ️ Layer {i}: Placing Bid @ {buy_price} | Ask @ {sell_price} (Qty: {qty})")
            
            # Execute Bid
            self.trade.execute_order(self.symbol, "Bid", buy_price, qty, post_only=True)
            # Execute Ask
            self.trade.execute_order(self.symbol, "Ask", sell_price, qty, post_only=True)
            
            # If we scaled down, we might run out of margin after 1st layer.
            # Update available margin estimate
            # Each order pair uses 2x Margin? No, one side fills first.
            # But exchange checks margin for both if open?
            # Usually Bid locks USDC, Ask locks Asset.
            # Assuming Bid locks margin.
            available_margin -= (TARGET_NOTIONAL / 10.0)
            if available_margin < 10.0:
                print("   ️ Margin exhausted. Stopping Grid expansion.")
                break
                
            time.sleep(0.5) # Avoid Rate Limit

