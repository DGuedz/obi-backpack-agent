import pandas as pd
import numpy as np
from backpack_data import BackpackData

class PhantomHFT:
    """
     PHANTOM HFT ENGINE
    Estratégia de Scalping baseada em SMC (Smart Money Concepts).
    Foco: Liquidity Sweeps, FVG Targeting e Execução Maker.
    """
    def __init__(self, data_api: BackpackData):
        self.data = data_api

    def find_nearest_fvg(self, klines, direction, min_size_pct=0.0005):
        """
        Encontra o FVG (Fair Value Gap) mais próximo e não mitigado.
        
        FVG Bearish (Target para Short): Espaço entre Low do Candle[i-1] e High do Candle[i+1].
        FVG Bullish (Target para Long): Espaço entre High do Candle[i-1] e Low do Candle[i+1].
        
        :param klines: Lista de candles (OHLCV).
        :param direction: 'up' (busca FVG Bearish acima para alvo de Long) ou 'down' (busca FVG Bullish abaixo para alvo de Short).
                          *NOTA*: Se estamos SHORT, o alvo é um FVG BULLISH (suporte) lá embaixo.
                          *NOTA*: Se estamos LONG, o alvo é um FVG BEARISH (resistência) lá em cima.
        :return: Preço do início do FVG (Alvo) ou None.
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        # Iterar do mais recente para o antigo para achar o "mais próximo"
        # Precisamos de pelo menos 3 candles para formar um FVG
        # FVG é formado no candle 'i'. O gap é entre i-1 e i+1.
        # Vamos iterar de len-2 até 1.
        
        found_fvg = None
        
        current_price = df['close'].iloc[-1]
        
        for i in range(len(df) - 2, 0, -1):
            prev_candle = df.iloc[i-1] # Candle i-1 (Esquerda)
            next_candle = df.iloc[i+1] # Candle i+1 (Direita) - Na verdade, o índice i é o candle do meio. 
            # Correção de nomenclatura:
            # Candle 0: Esquerda
            # Candle 1: Gap Candle (Grande)
            # Candle 2: Direita
            # O Gap está entre Candle 0 e Candle 2.
            
            candle_0 = df.iloc[i-1]
            candle_2 = df.iloc[i+1]
            
            # Se procuramos alvo para SHORT (queremos fechar lá embaixo), buscamos FVG Bullish (Suporte)
            if direction == 'down':
                # FVG Bullish: Gap entre High[0] e Low[2]
                # Condição: Low[2] > High[0]
                gap_top = candle_2['low']
                gap_bottom = candle_0['high']
                
                if gap_top > gap_bottom:
                    gap_size = (gap_top - gap_bottom) / gap_bottom
                    if gap_size >= min_size_pct and gap_top < current_price:
                        # Achamos um suporte não mitigado abaixo do preço
                        # Retornamos o topo do gap (primeiro toque)
                        return gap_top

            # Se procuramos alvo para LONG (queremos fechar lá em cima), buscamos FVG Bearish (Resistência)
            elif direction == 'up':
                # FVG Bearish: Gap entre Low[0] e High[2]
                # Condição: Low[0] > High[2]
                gap_top = candle_0['low']
                gap_bottom = candle_2['high']
                
                if gap_top > gap_bottom:
                    gap_size = (gap_top - gap_bottom) / gap_bottom
                    if gap_size >= min_size_pct and gap_bottom > current_price:
                        # Achamos uma resistência não mitigada acima do preço
                        # Retornamos o fundo do gap (primeiro toque)
                        return gap_bottom
                        
        return None

    def get_premium_discount_zone(self, klines):
        """
        Define se o preço atual está em Premium (>50%) ou Discount (<50%) do Range recente.
        """
        df = pd.DataFrame(klines)
        high = df['high'].astype(float).max()
        low = df['low'].astype(float).min()
        current = float(df['close'].iloc[-1])
        
        mid_point = (high + low) / 2
        
        if current > mid_point:
            return "PREMIUM" # Bom para Venda
        else:
            return "DISCOUNT" # Bom para Compra

    def detect_order_block(self, klines, direction):
        """
        Identifica o Order Block (OB) mais recente.
        OB Bullish: Última vela de baixa antes de um movimento forte de alta (BOS).
        OB Bearish: Última vela de alta antes de um movimento forte de baixa.
        """
        # Simplificação para HFT: Busca vela contrária antes de sequência de 3 velas na direção do BOS
        # Retorna o preço de abertura do OB (zona de interesse)
        return None # Implementação futura refinada

    def check_hft_scalp_setup(self, symbol, timeframe='5m'):
        """
        Verifica setup de Liquidity Sweep + Volume + Premium/Discount.
        """
        klines = self.data.get_klines(symbol, timeframe, limit=50)
        if not klines or len(klines) < 20:
            return None

        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        df['volume'] = df['volume'].astype(float)

        current = df.iloc[-1]
        
        # 1. Definir Estrutura Recente (Swing Points)
        window = df.iloc[-21:-1] # Janela anterior ao candle atual
        swing_high = window['high'].max()
        swing_low = window['low'].min()
        
        avg_volume = window['volume'].mean()
        
        # Filtro Premium/Discount
        pd_zone = self.get_premium_discount_zone(klines)
        
        setup = None

        # 2. Detectar Liquidity Sweep (BEARISH / BULL TRAP)
        # Preço rompeu o Topo, mas fechou abaixo dele.
        # Condição de Sweep: High > SwingHigh AND Close < SwingHigh
        if current['high'] > swing_high and current['close'] < swing_high:
            
            # Filtro SMC: Só vender em Premium
            if pd_zone == "DISCOUNT":
                # Ignorar venda barato
                return None
                
            # Validar Volume
            if current['volume'] > avg_volume * 1.5:
                target = self.find_nearest_fvg(klines, direction='down')
                if not target: target = current['close'] * 0.995
                
                setup = {
                    'symbol': symbol,
                    'signal': 'SHORT',
                    'entry_price': current['close'],
                    'stop_loss': current['high'] * 1.001,
                    'target': target,
                    'reason': 'Bearish Sweep (Premium Zone) + Vol',
                    'swing_point': swing_high
                }

        # 3. Detectar Liquidity Sweep (BULLISH / BEAR TRAP)
        elif current['low'] < swing_low and current['close'] > swing_low:
            
            # Filtro SMC: Só comprar em Discount
            if pd_zone == "PREMIUM":
                return None
                
            if current['volume'] > avg_volume * 1.5:
                target = self.find_nearest_fvg(klines, direction='up')
                if not target: target = current['close'] * 1.005

                setup = {
                    'symbol': symbol,
                    'signal': 'LONG',
                    'entry_price': current['close'],
                    'stop_loss': current['low'] * 0.999,
                    'target': target,
                    'reason': 'Bullish Sweep (Discount Zone) + Vol',
                    'swing_point': swing_low
                }
                
        return setup
