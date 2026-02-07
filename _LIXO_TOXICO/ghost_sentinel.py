import os
import time
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

class GhostSentinel:
    """
     GHOST SENTINEL (ANTI-HUNT PROTOCOL)
    Implementa Stop Loss Virtual que ignora 'agulhadas' (Liquidity Hunts).
    Só aciona se o candle FECHAR além do nível de invalidação.
    """
    def __init__(self):
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.private_key = os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(self.api_key, self.private_key)
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
        # Cache de níveis de invalidação
        self.invalidation_levels = {} 

    def calculate_invalidation_level(self, symbol, entry_price, side, timeframe="1h"):
        """
        Calcula o nível de invalidação baseado em estrutura de mercado (Swing Low/High).
        """
        klines = self.data.get_klines(symbol, interval=timeframe, limit=50)
        if not klines:
            return None
            
        df = pd.DataFrame(klines)
        df['low'] = df['low'].astype(float)
        df['high'] = df['high'].astype(float)
        
        # Swing Low/High dos últimos 20 candles
        if side == "Long":
            swing_low = df['low'].iloc[-20:].min()
            # Se o Swing Low estiver muito longe (>5%), usa 2.5% fixo do entry
            if entry_price > 0 and (entry_price - swing_low) / entry_price > 0.05:
                return entry_price * 0.975
            return swing_low
        else:
            swing_high = df['high'].iloc[-20:].max()
            if entry_price > 0 and (swing_high - entry_price) / entry_price > 0.05:
                return entry_price * 1.025
            return swing_high

    def check_positions(self):
        print(" Ghost Sentinel: Escaneando posições para proteção Anti-Hunt...")
        positions = self.data.get_positions()
        
        for pos in positions:
            symbol = pos['symbol']
            qty = float(pos['quantity'])
            if qty == 0: continue
            
            entry_price = float(pos['entryPrice'])
            side = "Long" if qty > 0 else "Short"
            
            # 1. Definir/Atualizar Nível de Invalidação
            if symbol not in self.invalidation_levels:
                level = self.calculate_invalidation_level(symbol, entry_price, side)
                if level:
                    self.invalidation_levels[symbol] = level
                    print(f"   ️ {symbol} ({side}): Ghost Stop definido em {level:.4f}")
            
            ghost_level = self.invalidation_levels.get(symbol)
            if not ghost_level: continue
            
            # 2. Verificar Fechamento do Candle (5m)
            # Pegar último candle FECHADO (penúltimo da lista)
            klines = self.data.get_klines(symbol, interval="5m", limit=2)
            if len(klines) < 2: continue
            
            last_closed_candle = klines[-2] # Penúltimo é o fechado
            close_price = float(last_closed_candle['close'])
            
            triggered = False
            if side == "Long" and close_price < ghost_level:
                print(f"    {symbol}: Fechamento ({close_price}) ABAIXO do Ghost Level ({ghost_level})!")
                triggered = True
            elif side == "Short" and close_price > ghost_level:
                print(f"    {symbol}: Fechamento ({close_price}) ACIMA do Ghost Level ({ghost_level})!")
                triggered = True
                
            if triggered:
                print(f"    EXECUÇÃO GHOST: Fechando posição a mercado para evitar desastre estrutural.")
                self.trade.close_position(symbol, qty)
                del self.invalidation_levels[symbol] # Reset
            else:
                # Log de monitoramento (opcional, pode ser verbose)
                # print(f"    {symbol}: Safe. Close {close_price} vs Level {ghost_level}")
                pass

    def run(self):
        print(" GHOST SENTINEL INICIADO.")
        while True:
            try:
                self.check_positions()
                time.sleep(10) # Verifica a cada 10s (suficiente para candle close)
            except Exception as e:
                print(f"Erro no Ghost Sentinel: {e}")
                time.sleep(5)

if __name__ == "__main__":
    sentinel = GhostSentinel()
    sentinel.run()
