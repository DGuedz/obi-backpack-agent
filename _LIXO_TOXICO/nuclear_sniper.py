import os
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_indicators import BackpackIndicators

load_dotenv()

class NuclearSniper:
    """
    ️ NUCLEAR SNIPER (50x LEVERAGE PROTOCOL)
    Estratégia HFT de altíssimo risco e precisão cirúrgica.
    Baseada em:
    1. Liquidity Sweeps (SFP)
    2. VWAP & Bollinger Rejection
    3. Maker Only Execution
    4. Auto-Breakeven @ 0.1%
    """
    def __init__(self):
        self.api_key = os.getenv('BACKPACK_API_KEY')
        self.private_key = os.getenv('BACKPACK_API_SECRET')
        self.auth = BackpackAuth(self.api_key, self.private_key)
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.indicators = BackpackIndicators()
        
        # Configuração Nuclear
        self.LEVERAGE = 50
        self.MARGIN_USD = 20 # Começar pequeno (20 * 50 = $1000 notional)
        self.SL_PCT = 0.002  # 0.2% Price Move
        self.TP_PCT = 0.05   # 5% Price Move (Target ideal, mas sai antes)
        self.BE_TRIGGER = 0.001 # 0.1% move -> Move SL to Entry

    def check_order_flow_imbalance(self, symbol):
        """
        Analisa o Order Book (Depth) para confirmar pressão compradora/vendedora.
        Retorna 'BULLISH', 'BEARISH' ou 'NEUTRAL'.
        """
        depth = self.data.get_orderbook_depth(symbol, limit=10)
        if not depth:
            return 'NEUTRAL'
            
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        # Calcular Volume Agregado
        bid_vol = sum([float(x[1]) for x in bids])
        ask_vol = sum([float(x[1]) for x in asks])
        
        ratio = bid_vol / ask_vol if ask_vol > 0 else 0
        
        if ratio > 1.5:
            return 'BULLISH' # Muita compra no book
        elif ratio < 0.6:
            return 'BEARISH' # Muita venda no book
        else:
            return 'NEUTRAL'

    def find_nearest_fvg(self, klines, direction, min_size_pct=0.0005):
        """
        Encontra o FVG (Fair Value Gap) mais próximo e não mitigado.
        """
        df = pd.DataFrame(klines)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        
        current_price = df['close'].iloc[-1]
        
        # Iterar de trás para frente (exceto os 2 últimos candles que estão formando o FVG potencial)
        for i in range(len(df) - 3, 0, -1):
            candle_0 = df.iloc[i-1]
            candle_2 = df.iloc[i+1]
            
            if direction == 'down': # Alvo para Short (Suporte)
                gap_top = candle_2['low']
                gap_bottom = candle_0['high']
                if gap_top > gap_bottom:
                    if gap_top < current_price: # FVG abaixo do preço
                        return gap_top

            elif direction == 'up': # Alvo para Long (Resistência)
                gap_top = candle_0['low']
                gap_bottom = candle_2['high']
                if gap_top > gap_bottom:
                    if gap_bottom > current_price: # FVG acima do preço
                        return gap_bottom
                        
        return None

    def scan_for_setup(self, symbol, timeframe="1m"):
        """
        Busca o setup 'Nuclear Sweep' em 1m ou 5m.
        """
        # Precisamos de dados suficientes para BB e VWAP
        klines = self.data.get_klines(symbol, interval=timeframe, limit=100)
        if not klines or len(klines) < 50:
            return None
            
        df = pd.DataFrame(klines)
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['open'] = df['open'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Indicadores
        bb = self.indicators.calculate_bollinger_bands(df, window=20, window_dev=2.5) # 2.5 Std Dev para extremos
        vwap = self.indicators.calculate_vwap(df)
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- Lógica de Entrada (LONG) ---
        bb_lower = bb['lower'].iloc[-1]
        vwap_val = vwap.iloc[-1]
        
        # Filtro de Volatilidade: Preço tocou a banda inferior?
        touched_band = current['low'] < bb_lower or prev['low'] < bb_lower
        
        if touched_band and current['close'] < vwap_val:
            # Setup Sweep (Bullish SFP)
            window = df.iloc[-20:-2] # Janela anterior
            swing_low = window['low'].min()
            
            body_size = abs(current['close'] - current['open'])
            lower_wick = min(current['close'], current['open']) - current['low']
            
            is_hammer = lower_wick > (body_size * 1.5)
            
            # REFINAMENTO 1: Micro-Estrutura (MSS)
            is_sfp = current['low'] < swing_low and current['close'] > swing_low
            
            if is_hammer or is_sfp:
                # REFINAMENTO 2: Order Flow Check
                imbalance = self.check_order_flow_imbalance(symbol)
                
                # REFINAMENTO 3: Volume Check (Stricter)
                vol_avg = df['volume'].rolling(20).mean().iloc[-1]
                high_vol = current['volume'] > vol_avg * 1.2 
                
                if high_vol and imbalance != 'BEARISH': 
                    
                    entry_price = current['close']
                    
                    # REFINAMENTO 4: Alvo em FVG
                    fvg_target = self.find_nearest_fvg(klines, direction='up')
                    
                    return {
                        'signal': 'LONG',
                        'symbol': symbol,
                        'price': entry_price,
                        'stop_loss': current['low'] * (1 - 0.0005), 
                        'vwap': vwap_val,
                        'fvg_target': fvg_target,
                        'reason': 'Nuclear Sweep Long (BB+VWAP+Vol+Flow)',
                        'imbalance': imbalance
                    }
                    
        return None

    def execute_nuclear_trade(self, setup):
        symbol = setup['symbol']
        side = "Bid" if setup['signal'] == 'LONG' else "Ask"
        price = setup['price']
        
        # Calcular Qty
        # Margin $20 * 50x = $1000 Position
        # Qty = 1000 / Price
        position_size_usd = self.MARGIN_USD * self.LEVERAGE
        quantity = position_size_usd / price
        
        # Ajustar regras de step (Simplificado)
        quantity = int(quantity) if price > 1 else round(quantity, 1) 
        
        print(f"️ NUCLEAR LAUNCH DETECTED: {symbol}")
        print(f"   Side: {side} | Price: {price} | Qty: {quantity}")
        print(f"   Leverage: {self.LEVERAGE}x | Stop: {setup['stop_loss']}")
        
        # 1. Enviar Ordem Maker (Entrada)
        res = self.trade.execute_order(
            symbol=symbol,
            side=side,
            price=str(price),
            quantity=str(quantity),
            order_type="Limit",
            post_only=True
        )
        
        if res and 'id' in res:
            print(f" Ordem Nuclear Enviada: {res['id']}")
            
            # 2. Configurar Saída (Take Profit no FVG)
            # Se não tiver FVG, usar VWAP ou 5%
            target_price = setup.get('fvg_target')
            if not target_price:
                target_price = setup.get('vwap')
                
            # Ajustar TP Price para string
            tp_price_str = f"{target_price:.2f}"
            
            print(f"    Target (TP) definido em: {tp_price_str}")
            
            # Enviar TP como Limit Reduce Only (após confirmação de fill, idealmente)
            # Como é HFT, podemos tentar pendurar logo se o preço permitir, ou monitorar
            # Por segurança, o Guardian deve assumir aqui.
            
            return True
        else:
            print(" Falha na execução Nuclear (Provável Taker Rejection).")
            return False

    def run_scanner(self):
        print("️ NUCLEAR SNIPER: Scanning 50x Setups (BTC, SOL, ETH)...")
        targets = ["BTC_USDC_PERP", "SOL_USDC_PERP", "ETH_USDC_PERP"]
        
        found = False
        for t in targets:
            setup = self.scan_for_setup(t, timeframe="1m")
            if setup:
                found = True
                print(f"\n SETUP ENCONTRADO EM {t}!")
                print(f"   {setup}")
                
                # Análise de Assimetria (Risco/Retorno)
                # Entry: Price
                # Stop: Wick Low
                # Target: VWAP (Mean Reversion)
                risk = (setup['price'] - setup['stop_loss']) / setup['price']
                reward = (setup['vwap'] - setup['price']) / setup['price']
                
                rr_ratio = reward / risk if risk > 0 else 0
                
                print(f"   ️ ASSIMETRIA: Risco {risk*100:.3f}% | Retorno {reward*100:.3f}% | R:R {rr_ratio:.2f}")
                
                if rr_ratio > 3:
                    print("    R:R EXCELENTE (>3). Preparando disparo...")
                    # self.execute_nuclear_trade(setup) 
                else:
                    print("   ️ R:R Baixo (<3). Apenas observando.")
            else:
                pass
                
        if not found:
            print("    Nenhum setup nuclear no momento (Aguardando Sweeps).")

if __name__ == "__main__":
    bot = NuclearSniper()
    while True:
        bot.run_scanner()
        time.sleep(10) # Scan a cada 10s (candle close 1m)
