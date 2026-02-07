import os
import sys
import pandas as pd
import requests
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class ExitStrategist:
    """
     EXIT STRATEGIST - HYPE_USDC_PERP
    Calcula o melhor ponto de saída (TP) baseado em:
    1. Estrutura de Mercado (Resistências Recentes)
    2. Fair Value Gaps (FVG Bearish)
    3. VWAP
    4. Níveis Psicológicos
    """
    def __init__(self):
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.private_key = os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(self.api_key, self.private_key)
        self.data = BackpackData(self.auth)
        self.SYMBOL = "HYPE_USDC_PERP"

    def calculate_indicators(self, df):
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # VWAP
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # EMA 20 (Mean Reversion Target)
        ema20 = df['close'].ewm(span=20).mean()
        
        return vwap.iloc[-1], ema20.iloc[-1]

    def find_bearish_fvgs(self, df):
        """
        Encontra FVGs Bearish acima do preço atual (Resistências).
        """
        fvgs = []
        current_price = df['close'].iloc[-1]
        
        # Iterar de trás para frente
        for i in range(len(df) - 2, 0, -1):
            candle_0 = df.iloc[i-1] # Low
            candle_2 = df.iloc[i+1] # High
            
            # FVG Bearish: Gap entre Low[0] e High[2]
            gap_top = candle_0['low']
            gap_bottom = candle_2['high']
            
            if gap_top > gap_bottom:
                if gap_bottom > current_price: # Só interessa se estiver acima
                    fvgs.append({
                        'bottom': gap_bottom,
                        'top': gap_top,
                        'mid': (gap_bottom + gap_top) / 2
                    })
                    
        return fvgs

    def analyze_exit(self):
        print(f" ANALISANDO SAÍDA PARA {self.SYMBOL}...")
        
        # 1. Dados Recentes (15m para estrutura)
        klines = self.data.get_klines(self.SYMBOL, interval="15m", limit=50)
        if not klines:
            print(" Erro ao obter dados.")
            return

        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_price = df['close'].iloc[-1]
        print(f"   Preço Atual: {current_price:.4f}")
        
        # 2. Indicadores Chave
        vwap, ema20 = self.calculate_indicators(df)
        print(f"   VWAP (Imã Institucional): {vwap:.4f}")
        print(f"   EMA 20 (Média Dinâmica): {ema20:.4f}")
        
        # 3. FVGs (Resistências de Fluxo)
        fvgs = self.find_bearish_fvgs(df)
        nearest_fvg = fvgs[0] if fvgs else None
        
        if nearest_fvg:
            print(f"    FVG Bearish Mais Próximo: {nearest_fvg['bottom']:.4f} - {nearest_fvg['top']:.4f}")
        else:
            print("   ️ Nenhum FVG Bearish próximo detectado nos últimos 50 candles.")

        # 4. Swing High Recente (Liquidez de Venda)
        # O último topo relevante
        swing_high = df['high'].iloc[-20:-1].max()
        print(f"   ️ Swing High (Liquidez): {swing_high:.4f}")
        
        # 5. Definição do Alvo Otimizado
        # Lógica: O preço tende a buscar a VWAP ou o início do FVG
        
        targets = []
        if nearest_fvg: targets.append(('FVG Bottom', nearest_fvg['bottom']))
        targets.append(('VWAP', vwap))
        targets.append(('EMA 20', ema20))
        targets.append(('Swing High', swing_high))
        
        # Filtrar alvos abaixo do preço (já passamos) e ordenar
        valid_targets = [t for t in targets if t[1] > current_price]
        valid_targets.sort(key=lambda x: x[1])
        
        print("\n ALVOS DE SAÍDA SUGERIDOS (Em Ordem):")
        if not valid_targets:
            print("   Estamos acima de todas as referências locais! (Blue Sky ou Reversão Total).")
            print("   Sugestão: Trailing Stop agressivo.")
        else:
            for i, t in enumerate(valid_targets):
                roi = (t[1] - current_price) / current_price * 100 * 10 # 10x leverage est
                print(f"   {i+1}. {t[0]}: {t[1]:.4f} (Est. ROI 10x: +{roi:.1f}%)")
                
            best_target = valid_targets[0]
            print(f"\n MELHOR SAÍDA TÁTICA (Primeira Barreira): {best_target[1]:.4f} ({best_target[0]})")
            print("   Recomendação: Posicionar TP Maker (Limit) levemente abaixo deste nível.")

if __name__ == "__main__":
    strategist = ExitStrategist()
    strategist.analyze_exit()
