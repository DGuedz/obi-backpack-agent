
import os
import sys
import time
from dotenv import load_dotenv

# Ensure we can import from legacy archive
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from technical_oracle import MarketProxyOracle

class SniperMakerProtocol:
    def __init__(self, symbol):
        self.symbol = symbol
        load_dotenv()
        self.data = BackpackData(None) # Auth handled internally or pass it if needed. 
        # Actually BackpackData needs auth for some calls, let's init properly
        from backpack_auth import BackpackAuth
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.oracle = MarketProxyOracle(symbol, self.auth, self.data)

    def calculate_perfect_entry(self, side):
        """
        Define o 'Centro do Alvo' (Preço Limite Perfeito).
        Não aceita o preço atual. Calcula o preço de suporte/resistência real.
        """
        # 1. Pega dados técnicos
        klines = self.data.get_klines(self.symbol, "15m", 100)
        current_price = float(self.data.get_ticker(self.symbol)['lastPrice'])
        
        if not klines:
            return str(current_price)

        # 2. Define o alvo baseado em Volatilidade (Bandas de Bollinger / VWAP)
        # Exemplo simples: Se Long, o alvo é o fundo do candle anterior ou suporte local
        if side == "Buy":
            # Lógica Sniper: Compra no pavio (Wick), não no corpo
            # Look at last 5 candles low
            target_price = min(float(k['low']) for k in klines[-5:]) 
            
            # Se o preço atual já estiver abaixo desse alvo (crash), usamos o atual - spread
            if target_price > current_price: 
                target_price = current_price * 0.9995 # Ajuste fino se o preço já caiu
            else:
                 # Se o preço atual está acima, penduramos no suporte (pavio)
                 pass

        else:
            # Short no topo do pavio recente
            target_price = max(float(k['high']) for k in klines[-5:])
            
            if target_price < current_price:
                target_price = current_price * 1.0005
            else:
                pass

        return f"{target_price:.4f}"

    def wait_and_shoot(self, side, quantity, stop_loss_pct=0.015):
        """
        O GATILHO DE SOBREVIVÊNCIA.
        Só dispara se a confluência existir e APENAS como Maker.
        """
        side_str = "Buy" if side == "Bid" else "Sell"
        print(f" [SNIPER] Mirando {self.symbol} ({side_str})... Aguardando alinhamento...")

        # 0. PRE-FLIGHT NARRATIVE CHECK (GUARDIAN)
        # Display the narrative to the log so the user sees "WHY" we are proceeding or aborting.
        narrative = self.oracle.get_market_narrative()
        if narrative:
            print(f"    MARKET NARRATIVE: {narrative['status']} (OBI: {narrative['obi']:.2f})")
            print(f"      Walls: {narrative['bid_walls']} Bids vs {narrative['ask_walls']} Asks")
        else:
            print("   ️ Narrative Unavailable. Proceeding with caution...")

        # 1. Validação do Oráculo (A Confluência)
        # OBI e Funding devem estar alinhados. Se não, aborta.
        # side param for validate_entry expects 'Bid' or 'Ask' based on technical_oracle.py analysis
        if not self.oracle.validate_entry(side):
            print(" [ABORT] Oráculo negou a entrada (Falta Confluência).")
            return False

        # 2. Cálculo do Alvo
        target_price_str = self.calculate_perfect_entry(side_str)
        target_price = float(target_price_str)
        
        # Cálculo do Stop Loss Atômico (Baseado no Alvo, não no preço atual)
        if side == "Bid" or side == "Buy":
            sl_price = target_price * (1 - stop_loss_pct)
        else:
            sl_price = target_price * (1 + stop_loss_pct)

        print(f" [LOCK] Alvo Travado: ${target_price:.4f} | SL Atômico: ${sl_price:.4f}")

        # 3. O TIRO (Execução Post-Only Obrigatória)
        try:
            # execute_order signature: symbol, side, price, quantity, order_type="Limit", ...
            # We need to ensure post_only=True is passed.
            order = self.trade.execute_order(
                symbol=self.symbol,
                side=side, # 'Bid' or 'Ask'
                price=str(target_price),
                quantity=str(quantity),
                order_type="Limit",           # OBRIGATÓRIO: Limit
                post_only=True,               # OBRIGATÓRIO: A Trava de Segurança
                stop_loss=sl_price            # Atomicidade
            )
            
            if order and 'id' in order:
                print(f" [SNIPER] Armadilha colocada no livro (ID: {order['id']}). Esperando o mercado vir até nós.")
                return True
            else:
                print(f"️ Ordem não confirmada: {order}")
                
        except Exception as e:
            if "PostOnly" in str(e) or "post-only" in str(e).lower():
                print("️ [DEFESA] Ordem rejeitada pelo PostOnly. O preço correu. Não perseguimos.")
                # Aqui o bot NÃO tenta entrar de novo imediatamente. Ele espera o próximo ciclo.
            else:
                print(f" Erro de execução: {e}")
        
        return False
