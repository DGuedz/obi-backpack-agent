import pandas as pd
import numpy as np
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

class SmartMoneyEngine:
    """
     ENGINE DE SMART MONEY & WYCKOFF
    Implementa lógica institucional: Liquidity Sweeps, VSA, SFP e Execução Passiva.
    """
    def __init__(self, data_api: BackpackData, trade_api: BackpackTrade):
        self.data = data_api
        self.trade = trade_api

    def detect_liquidity_walls(self, symbol, depth_limit=100):
        """
        Identifica 'Paredes' de liquidez no Order Book (Limit Orders Clusters).
        Onde o varejo vê Resistência, nós vemos ALVO DE LIQUIDEZ.
        Retorna (bid_walls_df, ask_walls_df).
        """
        depth = self.data.get_orderbook_depth(symbol, limit=depth_limit)
        if not depth:
            return pd.DataFrame(), pd.DataFrame()

        bids = depth.get('bids', []) # [[price, qty], ...]
        asks = depth.get('asks', [])

        if not bids or not asks:
            return pd.DataFrame(), pd.DataFrame()

        # Convert to DataFrame
        df_bids = pd.DataFrame(bids, columns=['price', 'quantity']).astype(float)
        df_asks = pd.DataFrame(asks, columns=['price', 'quantity']).astype(float)

        # Calculate local average quantity to find anomalies (Whale Orders)
        avg_bid_qty = df_bids['quantity'].mean()
        avg_ask_qty = df_asks['quantity'].mean()

        # Threshold: Volume > 3x a média local = Parede Institucional
        WALL_THRESHOLD = 3.0 

        bid_walls = df_bids[df_bids['quantity'] > avg_bid_qty * WALL_THRESHOLD].copy()
        ask_walls = df_asks[df_asks['quantity'] > avg_ask_qty * WALL_THRESHOLD].copy()
        
        # Adicionar coluna de valor total ($)
        if not bid_walls.empty:
            bid_walls['value_usd'] = bid_walls['price'] * bid_walls['quantity']
            
        if not ask_walls.empty:
            ask_walls['value_usd'] = ask_walls['price'] * ask_walls['quantity']

        return bid_walls, ask_walls

    def validate_vsa_breakout(self, symbol, timeframe="5m"):
        """
        VSA (Volume Spread Analysis) - Filtro de Indução.
        Um rompimento sem volume é FALSO (Trap).
        Retorna (is_valid, current_vol, avg_vol).
        """
        klines = self.data.get_klines(symbol, interval=timeframe, limit=50)
        if not klines:
            return False, 0, 0

        df = pd.DataFrame(klines)
        df['volume'] = df['volume'].astype(float)
        
        current_volume = df['volume'].iloc[-1]
        vol_sma_20 = df['volume'].rolling(window=20).mean().iloc[-1]

        # Regra VSA: Effort vs Result
        # Rompimento real exige Volume > 2x Média
        is_valid = current_volume > (vol_sma_20 * 2.0)
        
        return is_valid, current_volume, vol_sma_20

    def detect_sfp(self, symbol, timeframe="15m"):
        """
        SFP (Swing Failure Pattern) - O Setup de Ouro do Smart Money.
        Detecta quando o preço captura liquidez (rompe topo/fundo) mas rejeita (fecha dentro).
        Retorna: "BEARISH_SFP", "BULLISH_SFP" ou None.
        """
        klines = self.data.get_klines(symbol, interval=timeframe, limit=50)
        if not klines:
            return None

        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        
        # Definir Swing High/Low recente (ex: max/min dos últimos 20 candles, ignorando o atual)
        lookback = 20
        recent_high = df['high'].iloc[-lookback:-1].max()
        recent_low = df['low'].iloc[-lookback:-1].min()
        
        current = df.iloc[-1]
        
        # SFP Bearish (Bull Trap / Liquidity Grab em Topo)
        # Preço foi ACIMA do topo anterior (High > Recent High)
        # Mas fechou ABAIXO (Close < Recent High)
        if current['high'] > recent_high and current['close'] < recent_high:
            return "BEARISH_SFP"
            
        # SFP Bullish (Bear Trap / Liquidity Grab em Fundo)
        # Preço foi ABAIXO do fundo anterior (Low < Recent Low)
        # Mas fechou ACIMA (Close > Recent Low)
        if current['low'] < recent_low and current['close'] > recent_low:
            return "BULLISH_SFP"
            
        return None

    def execute_passive_entry(self, symbol, side, price, qty):
        """
        Execução Passiva (Maker Only).
        Instituições não pagam spread, elas ganham spread.
        """
        print(f" SMART MONEY ENTRY: {side} {symbol} @ {price} (PostOnly)")
        return self.trade.execute_order(
            symbol=symbol,
            side=side,
            price=str(price),
            quantity=str(qty),
            order_type="Limit",
            post_only=True # OBRIGATÓRIO: Se for taker, a ordem é rejeitada/cancelada.
        )
