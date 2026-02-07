from backpack_data import BackpackData
from advanced_indicators import AdvancedIndicators

class ExhaustionSniper:
    """
    Agente Sniper de Exaustão (The Night Owl)
    Missão: Detectar reversões técnicas usando RSI + EMA para entradas cirúrgicas.
    Contexto: "Visão Noturna", buscando ativos que "esticaram o elástico" demais.
    """
    def __init__(self, data_client: BackpackData):
        self.data = data_client
        self.indicators = AdvancedIndicators(data_client)

    def hunt(self, symbol, timeframe='15m'):
        """
        Scans a specific symbol for Exhaustion Reversal signals.
        Returns signal dict if found, None otherwise.
        """
        print(f" Night Owl: Stalking {symbol} ({timeframe})...")
        
        # 1. Volume Check (> $10M)
        try:
            ticker = self.data.get_ticker(symbol)
            if not ticker:
                return None
            
            # Handle different API keys for volume
            quote_vol = float(ticker.get('quoteVolume', 0))
            if quote_vol == 0:
                 vol = float(ticker.get('volume', 0))
                 price = float(ticker.get('lastPrice', 0))
                 quote_vol = vol * price
                 
            if quote_vol < 10000000:
                # Silent fail to avoid spam
                # print(f"   ️ Owl: Volume Low (${quote_vol/1000000:.1f}M). Skipping.")
                return None
        except Exception as e:
            print(f"   ️ Owl Error (Data): {e}")
            return None
            
        # 2. Technical Analysis (RSI + EMA)
        signal_data = self.indicators.analyze_exhaustion_setup(symbol, timeframe)
        signal = signal_data.get('signal', 'NEUTRAL')
        
        if signal != "NEUTRAL":
            print(f"    OWL DETECTED PREY: {symbol} [{signal}]")
            print(f"      Stoch K: {signal_data.get('stoch_k', 0):.1f}")
            print(f"      Deviation: {signal_data.get('deviation_pct', 0):.2f}% vs EMA100")
            
            return {
                "symbol": symbol,
                "signal": signal,
                "stoch_k": signal_data.get('stoch_k'),
                "deviation_pct": signal_data.get('deviation_pct'),
                "ema100": signal_data.get('ema100'),
                "price": float(ticker.get('lastPrice', 0))
            }
            
        return None
