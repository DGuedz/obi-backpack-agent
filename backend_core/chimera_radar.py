import sys
import os
import time
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Configurar Paths
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.gatekeeper import Gatekeeper

# Configurações de Exibição
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

class ChimeraRadar:
    """
     CHIMERA RADAR (V3)
    Escaneia o mercado em busca de Confluência Total (Gatekeeper) + Volatilidade Ideal (ATR).
    Identifica onde apontar o Sniper.
    """
    def __init__(self):
        load_dotenv()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.gatekeeper = Gatekeeper(self.data)
        
        # Lista de Ativos Prioritários (Ou scan geral)
        self.priority_assets = [
            "SOL_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP", 
            "JUP_USDC_PERP", "HYPE_USDC_PERP", "SUI_USDC_PERP",
            "DOGE_USDC_PERP", "WIF_USDC_PERP", "RENDER_USDC_PERP"
        ]

    def get_atr_volatility(self, symbol):
        """Calcula ATR % (Volatilidade) e EMA50 (Tendência)."""
        try:
            klines = self.data.get_klines(symbol, "15m", limit=20)
            if not klines: return 0, 0, 0
            
            df = pd.DataFrame(klines)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            
            # ATR
            df['tr'] = df['high'] - df['low']
            atr = df['tr'].mean()
            current_price = df.iloc[-1]['close']
            atr_pct = atr / current_price
            
            # EMA 50 (usando 60 candles 1h se possível, mas aqui usando os dados que temos ou fetch separado)
            # Para tendência macro, melhor pegar 1h.
            return atr_pct * 100, current_price
        except:
            return 0, 0

    def get_trend_bias(self, symbol):
        """Define viés (Buy/Sell) baseado na EMA50 de 1H."""
        try:
            klines = self.data.get_klines(symbol, "1h", limit=60)
            if not klines: return "Neutral", 0
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            last_price = df.iloc[-1]['close']
            
            if last_price > ema_50: return "Buy", last_price
            return "Sell", last_price
        except:
            return "Neutral", 0

    def scan(self):
        print("\n CHIMERA RADAR: Escaneando o Mercado por Oportunidades...")
        print(f"    {datetime.now().strftime('%H:%M:%S')} | Volatilidade Alvo: >0.4% (15m)")
        print("-" * 80)
        print(f"{'SYMBOL':<15} {'SIDE':<5} {'PRICE':<10} {'VOL(15m)':<10} {'OBI':<8} {'SPREAD':<8} {'STATUS'}")
        print("-" * 80)
        
        candidates = []
        
        for symbol in self.priority_assets:
            # 1. Identificar Tendência
            bias, price = self.get_trend_bias(symbol)
            if bias == "Neutral": continue
            
            # 2. Calcular Volatilidade
            vol_pct, _ = self.get_atr_volatility(symbol)
            
            # 3. Check Gatekeeper (Confluência)
            # Gatekeeper retorna (bool, reason, context)
            approved, reason, context = self.gatekeeper.check_confluence(symbol, bias)
            
            obi = context.get('obi', 0)
            spread = context.get('spread', 0) * 100
            
            # Formatação de Status
            if approved:
                status = " SNIPER READY"
                candidates.append((symbol, bias, vol_pct))
            else:
                # Simplificar razão para caber na tabela
                short_reason = reason.split('|')[0][:20]
                status = f" {short_reason}"
                
            # Cor no terminal (Simulada com caracteres)
            print(f"{symbol:<15} {bias:<5} {price:<10.4f} {vol_pct:>6.3f}%   {obi:>6.2f}   {spread:>6.3f}%   {status}")
            
            time.sleep(0.2) # Evitar Rate Limit
            
        print("-" * 80)
        
        if candidates:
            best = sorted(candidates, key=lambda x: x[2], reverse=True)[0] # Maior volatilidade
            print(f"\n MELHOR ALVO: {best[0]} ({best[1]}) - Volatilidade: {best[2]:.3f}%")
            print(f"    Sugestão: python3 confluence_sniper.py {best[0]}")
        else:
            print("\n Nenhum ativo alinhado no momento. O Mercado está indeciso ou sem fluxo.")

if __name__ == "__main__":
    radar = ChimeraRadar()
    while True:
        radar.scan()
        print("\n⏳ Aguardando 30s para próximo scan... (Ctrl+C para parar)")
        time.sleep(30)
