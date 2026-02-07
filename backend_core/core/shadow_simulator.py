
import time
import pandas as pd
from core.backpack_transport import BackpackTransport

class ShadowSimulator:
    """
     SHADOW SIMULATOR (Protocolo 2 de 3)
    Executa simulações em background a cada 1 minuto.
    Regra: O ativo só é liberado para trade real se tiver vencido 2 das últimas 3 simulações.
    """
    def __init__(self, transport: BackpackTransport):
        self.transport = transport
        self.approved_assets = {} # {symbol: timestamp}
        self.APPROVAL_TTL = 60 # Validade da aprovação: 1 minuto
        
        # Sim Parameters
        self.SL_PCT = 0.001 # 0.1% Price Move (1% Margin @ 10x)
        self.TP_PCT = 0.005 # 0.5% Price Move (5% Margin @ 10x)

    def run_simulation_cycle(self, targets, gatekeeper=None):
        """
        Roda a simulação para todos os alvos. Retorna lista de aprovados.
        Inclui verificação de Indicadores On-Chain em Tempo Real (Gatekeeper) para logging.
        """
        print("\n SHADOW SIMULATOR: Iniciando Bateria de Testes (1m)...")
        approved = []
        
        for symbol in targets:
            # 1. Simulação Histórica (Backtest Recente)
            sim_passed = self._simulate_asset(symbol)
            
            # 2. Indicadores On-Chain em Tempo Real (Gatekeeper Check)
            gk_status = "N/A"
            if gatekeeper:
                # Checa Long e Short apenas para ver status do Book/Volume
                # Não bloqueia a simulação (que é histórica), mas informa o operador
                try:
                    # Verifica dados básicos de Ticker/Depth
                    ticker = self.transport.get_ticker(symbol)
                    quote_vol = float(ticker.get('quoteVolume', 0)) if ticker else 0
                    
                    depth = self.transport.get_orderbook_depth(symbol)
                    bids = depth.get('bids', []) if depth else []
                    asks = depth.get('asks', []) if depth else []
                    
                    if bids and asks:
                        best_bid = float(bids[-1][0])
                        best_ask = float(asks[0][0])
                        spread = (best_ask - best_bid) / best_bid
                        gk_status = f"Spread: {spread*100:.3f}% | Vol: ${quote_vol/1_000_000:.1f}M"
                    else:
                        gk_status = "Book Vazio"
                except Exception as e:
                    gk_status = f"Erro GK: {str(e)[:20]}"

            print(f"   ℹ️  {symbol} Real-Time Data: [{gk_status}]")

            if sim_passed:
                print(f"    {symbol}: APROVADO no Teste de Combate (2/3 Vitórias)")
                self.approved_assets[symbol] = time.time()
                approved.append(symbol)
            else:
                print(f"    {symbol}: REPROVADO na Simulação")
                
        return approved

    def is_asset_approved(self, symbol):
        """
        Verifica se o ativo está na whitelist válida.
        """
        timestamp = self.approved_assets.get(symbol)
        if not timestamp: return False
        
        if time.time() - timestamp <= self.APPROVAL_TTL:
            return True
        else:
            return False # Expirou

    def _simulate_asset(self, symbol):
        """
        Backtest rápido nos últimos candles de 1m.
        Busca os últimos 3 sinais válidos e verifica o resultado (Win/Loss).
        """
        try:
            # Pegar dados recentes (1m candles) - Aumentado para 300 para garantir sinais
            klines = self.transport.get_klines(symbol, "1m", limit=300)
            if not klines: return False
            
            df = pd.DataFrame(klines)
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['open'] = df['open'].astype(float)
            
            # Indicadores
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            signals = []
            
            # Analisar histórico recente para encontrar os últimos 3 sinais
            # Iterar de trás para frente (Do mais recente para o antigo)
            # Começamos do penúltimo candle (len-2) pois o último (len-1) está aberto
            # Precisamos de espaço para verificar o resultado (pelo menos 1 candle futuro)
            
            scan_start = len(df) - 2 
            scan_end = 50 # Precisamos de 50 candles para EMA
            
            for i in range(scan_start, scan_end, -1):
                if len(signals) >= 3: break
                
                row = df.iloc[i]
                price = row['close']
                
                signal_type = None
                # LONG: Preço > EMA50 e RSI < 45 (Pullback Moderado)
                if price > row['ema50'] and row['rsi'] < 45:
                    signal_type = "LONG"
                # SHORT: Preço < EMA50 e RSI > 55 (Pullback Moderado)
                elif price < row['ema50'] and row['rsi'] > 55:
                    signal_type = "SHORT"
                    
                if signal_type:
                    # Simular Resultado (Olhando candles futuros)
                    outcome = "LOSS" 
                    
                    entry = price
                    sl = entry * (1 - self.SL_PCT) if signal_type == "LONG" else entry * (1 + self.SL_PCT)
                    tp = entry * (1 + self.TP_PCT) if signal_type == "LONG" else entry * (1 - self.TP_PCT)
                    
                    # Checar próximos 10 candles (janela de 10 min para scalp)
                    for j in range(1, 11):
                        if i + j >= len(df): break # Não temos dados futuros suficientes (candle muito recente)
                        
                        future = df.iloc[i+j]
                        
                        if signal_type == "LONG":
                            if future['low'] <= sl:
                                outcome = "LOSS"
                                break
                            elif future['high'] >= tp:
                                outcome = "WIN"
                                break
                        else:
                            if future['high'] >= sl:
                                outcome = "LOSS"
                                break
                            elif future['low'] <= tp:
                                outcome = "WIN"
                                break
                    
                    # Se não atingiu TP nem SL em 10 candles, consideramos LOSS (Time Stop) ou Breakeven?
                    # Para ser conservador: LOSS (Capital preso)
                    
                    signals.append(outcome)
                    print(f"      Signal found at {i}: {signal_type} -> {outcome}") 

            # Avaliar Resultado: Precisa de pelo menos 2 Wins
            wins = signals.count("WIN")
            total = len(signals)
            
            if total > 0:
                win_rate = (wins/total)*100
                print(f"    {symbol} Simulação: {wins}/{total} Wins ({win_rate:.0f}%)")
            else:
                print(f"   ️ {symbol} Simulação: Nenhum setup encontrado nas últimas 4h.")
                return False

            if total >= 1 and wins >= 2: # Se achou 3, precisa de 2. Se achou 2, precisa de 2.
                return True
            elif total == 1 and wins == 1: # Se só achou 1 sinal recente e foi WIN, damos chance? Não, regra é 2/3.
                return False
            
            return False
            
        except Exception as e:
            print(f"   ️ Erro na Simulação de {symbol}: {e}")
            return False
