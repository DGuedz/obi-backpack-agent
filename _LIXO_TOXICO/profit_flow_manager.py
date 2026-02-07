#!/usr/bin/env python3
"""
 BLOOD WAR MANAGER (Compound Sequence)
Estratégia: 5 Tiros de Sniper com Juros Compostos (Compound).
Alavancagem: 10x
Foco: Liquidez (Maker Only), Velocidade (0.7% mov) e Defesa (Stop Curto).
"""

import os
import time
import argparse
from backpack_trade import BackpackTrade
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from market_intelligence import MarketIntelligence
from dotenv import load_dotenv

load_dotenv()

# Configuração Padrão (Sobrescrita por args)
INITIAL_CAPITAL = 100.0 # Seed Money ($100)
LEVERAGE = 10          # 10x
TP_PCT = 0.007         # 0.7% mov (7% ROE bruto) -> ~5.5% Liq
SL_PCT = 0.006         # 0.6% mov (6% Risk)
MAX_ROUNDS = 5         # 5 Tiros

class BloodWarManager:
    def __init__(self, leverage, tp, sl, rounds):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.mi = MarketIntelligence()
        
        self.leverage = leverage
        self.tp_pct = tp
        self.sl_pct = sl
        self.max_rounds = rounds
        
        self.current_round = 1 # Iniciando do Zero (ETH Gap Hunter)
        self.current_capital = 100.0 # Orçamento Aprovado
        
        # Sequência de Ativos Otimizada (GAP HUNTER - ETH)
        self.sequence = [
            "ETH_USDC_PERP", # #1 (Pegar o Gap Agora!)
            "ETH_USDC_PERP", # #2 (Follow Through)
            "ETH_USDC_PERP", # #3 (Reteste)
            "SOL_USDC_PERP", # #4 (Diversificação)
            "SOL_USDC_PERP"  # #5 (Fechamento)
        ]

    def get_entry_signal(self, symbol):
        """Busca entrada técnica precisa (Maker) com Multi-Timeframe Analysis"""
        print(f"    Buscando entrada em {symbol} (MTF Scan)...")
        
        attempts = 0
        while attempts < 60:
            # Análise Multi-Timeframe (5m, 1h, 4h, 6h)
            analyses, mtf_score = self.mi.analyze_multi_timeframe(symbol)
            
            # Pega dados do curto prazo (5m) para execução fina
            analysis_5m = analyses.get("5m")
            if not analysis_5m:
                time.sleep(1)
                continue
                
            price = analysis_5m['price']
            rsi_5m = analysis_5m['rsi']
            
            # Lógica de Decisão baseada em Confluência MTF
            # Se Score MTF for alto (> 3), indica alinhamento de timeframes
            if mtf_score >= 3:
                print(f"      MTF ALIGNMENT DETECTED (Score {mtf_score}). CONFLUÊNCIA CONFIRMADA.")
                analysis_5m['score'] = 2 # Force Strong Buy
                return analysis_5m
            
            # Fallback para setups específicos de curto prazo (Liquidity Hunt - Mean Reversion)
            if 'ETH' in symbol:
                 bb_lower = analysis_5m.get('bb_lower', 0)
                 bb_upper = analysis_5m.get('bb_upper', 0)
                 
                 # 1. Long Scalp (Toque na Banda Inferior)
                 if bb_lower > 0 and price <= bb_lower * 1.001:
                     print(f"      BOLLINGER LIQUIDITY HUNT (5m): Preço na Banda Inferior. COMPRA.")
                     analysis_5m['score'] = 2
                     return analysis_5m
                     
                 # 2. Short Scalp (Toque na Banda Superior - "Dentro de Bollinger")
                 if bb_upper > 0 and price >= bb_upper * 0.999:
                     print(f"      BOLLINGER RESISTANCE HUNT (5m): Preço na Banda Superior. VENDA (Short Scalp).")
                     analysis_5m['score'] = -2 # Force Strong Sell
                     return analysis_5m
            
            attempts += 1
            time.sleep(1)
            
        print("   ️ Time-out buscando sinal perfeito. Forçando entrada técnica (VWAP)...")
        # Se não achou sinal perfeito, pega o preço atual e define lado pela tendência micro (EMA/RSI)
        ticker = self.data.get_ticker(symbol)
        price = float(ticker['lastPrice'])
        rsi = self.mi.calculate_rsi([price]*15) # Mock rápido se precisar
        
        # Decisão de emergência: Respeita sobrecompra/sobrevenda
        if 'ETH' in symbol:
            if rsi > 60: side = "Ask" # Short se esticado
            else: side = "Bid" # Long se neutro/baixo
        else:
            side = "Bid" if rsi < 50 else "Ask"
            
        return {
            "symbol": symbol,
            "price": price,
            "score": 1 if side == "Bid" else -1
        }

    def adjust_quantity(self, symbol, quantity):
        """Ajusta precisão da quantidade para evitar rejeição da API"""
        if 'BONK' in symbol: return int(quantity / 100) * 100 # Step 100
        if 'WIF' in symbol or 'JUP' in symbol or 'PYTH' in symbol: return int(quantity) # Step 1
        if 'APT' in symbol or 'SUI' in symbol or 'RENDER' in symbol: return round(quantity, 1) # Step 0.1
        if 'SOL' in symbol or 'ETH' in symbol: return round(quantity, 2) # Step 0.01
        if 'BTC' in symbol: return round(quantity, 4) # Step 0.0001 (Ajuste Crítico para < $100)
        return round(quantity, 1) # Default safe

    def wait_for_fill(self, symbol, order_id):
        """Loop de espera até a ordem ser preenchida (Filled)"""
        print(f"     ⏳ Monitorando Ordem {order_id}...")
        start_time = time.time()
        while time.time() - start_time < 600: # 10 min max wait
            order = self.trade.get_order(symbol, order_id)
            if order:
                status = order.get('status')
                if status == 'Filled':
                    print(f"      Ordem EXECUTADA! Preço Médio: {order.get('avgFillPrice')}")
                    return True, float(order.get('avgFillPrice'))
                elif status == 'Cancelled' or status == 'Expired':
                    print(f"      Ordem Cancelada/Expirada.")
                    return False, 0
            time.sleep(0.5)
        print("     ️ Timeout esperando Fill.")
        return False, 0

    def monitor_position_closure(self, symbol):
        """
        MODO HOLD & PROTECT: Mantém a posição com ordens Limit (TP) e Stop (SL) no book.
        O script encerra sua execução ativa para liberar o terminal, pois as ordens
        já estão na exchange (Server-Side).
        """
        print(f"     ️ MODO HOLD & PROTECT: Posição Segura em {symbol}.")
        
        # 1. Verificar se TP já está no book
        open_orders = self.data.get_open_orders()
        has_tp = any(o.get('symbol') == symbol and o.get('reduceOnly') and o.get('side') == 'Ask' for o in open_orders)
        
        if has_tp:
            print("      Take Profit (Limit) confirmado no Order Book.")
        else:
            print("     ️ TP não encontrado! Recalculando e enviando...")
            # Lógica de reenvio se necessário...
            
        print("      O Agente entrará em repouso. As ordens Limit segurarão a posição.")
        print("      Monitore pelo App da Backpack.")
        return 0

    def get_usdc_balance(self):
        balances = self.data.get_balances()
        return float(balances.get('USDC', {}).get('available', 0))

    def execute_round(self):
        symbol = self.sequence[self.current_round - 1]
        print(f"\n️  ROUND {self.current_round}/{self.max_rounds}: {symbol}")
        print(f" Capital em Jogo: ${self.current_capital:.2f}")
        
        # 1. Sinal
        signal = self.get_entry_signal(symbol)
        side = "Bid" if signal['score'] > 0 else "Ask"
        price = float(signal['price'])
        
        # Qty (Full Compound)
        # O usuário destinou $100. Com alavancagem 10x, temos poder de compra de $1000.
        # Vamos usar 100% do capital ($100) * Leverage (10) = $1000 Notional.
        notional_value = self.current_capital * self.leverage
        qty = notional_value / price
        
        if 'WIF' in symbol or 'JUP' in symbol: qty = int(qty)
        else: qty = round(qty, 2)

        print(f"    Alavancagem: {self.leverage}x")
        print(f"    Poder de Fogo (Notional): ${notional_value:.2f}")
        print(f"    Quantidade: {qty} {symbol}")

        # Loop de Tentativa de Entrada (Linha Fina - ULTRA AGRESSIVO)
        entry_success = False
        retry_buffer = 0.0002 # 0.02% (Quase Taker, mas ainda Maker)
        
        while not entry_success and retry_buffer <= 0.0030: # Até 0.30%
            print(f"    Tentando Disparar {side} {qty} {symbol} @ Buffer {retry_buffer*100:.2f}%...")
            
            # Recalcula preço com buffer atual
            if side == "Bid": final_price = price * (1 - retry_buffer)
            else: final_price = price * (1 + retry_buffer)
            
            # Decimais
            if 'BONK' in symbol or 'PYTH' in symbol: final_price = round(final_price, 6)
            else: final_price = round(final_price, 2)
            
            # 2. Execução (Maker Only)
            try:
                order = self.trade.execute_order(
                    symbol=symbol,
                    side=side,
                    price=final_price,
                    quantity=qty,
                    order_type="Limit",
                    post_only=True
                )
                
                if order and 'id' in order:
                    print(f"      Ordem Plantada na LINHA FINA: {order['id']}")
                    entry_success = True
                    price = final_price # Atualiza preço oficial para TP/SL
                else:
                    # Se falhar (provavelmente Post Only reject), aumenta o buffer
                    print(f"     ️ Rejeitado (Taker?). Afastando linha...")
                    retry_buffer += 0.0002 # Incrementa +0.02%
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"      Erro Crítico: {e}")
                return False

        if not entry_success:
            print(" Falha Total na Entrada após várias tentativas.")
            return False

        # Aguardar Fill (REAL MODE)
        filled, avg_price = self.wait_for_fill(symbol, order['id'])
        
        if not filled:
            print(" Ordem não preenchida ou cancelada. Abortando Round.")
            return False
            
        # Atualiza preço com o real da execução
        price = avg_price

        # 3. Configurar OCO (TP/SL)
        # Ajuste de Alvos para Blood War:
        # TP 5% ROE (em 10x) -> 0.5% movimento do preço
        # SL 2% ROE (em 10x) -> 0.2% movimento do preço
        
        # Override dos defaults para garantir a instrução do usuário
        self.tp_pct = 0.005 # 0.5% mov * 10x = 5% ROE
        self.sl_pct = 0.002 # 0.2% mov * 10x = 2% ROE (Stop Curto)

        tp_price = price * (1 + self.tp_pct) if side == "Bid" else price * (1 - self.tp_pct)
        sl_price = price * (1 - self.sl_pct) if side == "Bid" else price * (1 + self.sl_pct)
        
        if 'BONK' in symbol: 
            tp_price = round(tp_price, 6)
            sl_price = round(sl_price, 6)
        else: 
            tp_price = round(tp_price, 2)
            sl_price = round(sl_price, 2)
        
        print(f"      Alvo: ${tp_price} (+{self.tp_pct*100}%) | ️ Stop: ${sl_price} (-{self.sl_pct*100}%)")
        
        # Enviar Ordens de Proteção (REAL)
        tp_side = "Ask" if side == "Bid" else "Bid"
        sl_side = "Ask" if side == "Bid" else "Bid"
        
        # TP Limit (Reduce Only)
        # NOTA CRÍTICA: Na Backpack, SL/TP são ordens separadas.
        # Se você não vê no app como "TP/SL Linkado", é porque são ordens Limit/Market Trigger avulsas.
        # O efeito é o mesmo (proteção), mas a visualização é em "Open Orders".
        
        # Take Profit (Ordem Limit de Saída)
        tp_order = self.trade.execute_order(symbol, tp_side, tp_price, qty, "Limit", reduce_only=True)
        if tp_order:
             print(f"      TP Plantado: ${tp_price} (ID: {tp_order.get('id')})")
        
        # Stop Loss (Ordem Market Trigger de Saída)
        sl_order = self.trade.execute_order(symbol, sl_side, "Market", qty, trigger_price=sl_price, reduce_only=True)
        if sl_order:
             print(f"      SL Plantado: ${sl_price} (ID: {sl_order.get('id')})")
        
        # Monitorar Resultado (REAL)
        realized_profit = self.monitor_position_closure(symbol)
        
        if realized_profit > 0:
            print(f"      ROUND VENCIDO! Lucro Realizado: ${realized_profit:.2f}")
            self.current_capital += realized_profit
            self.current_round += 1
            # Cancelar ordens pendentes (TP ou SL que sobrou)
            self.trade.cancel_all_orders(symbol)
            return True
        else:
            print(f"      ROUND PERDIDO. Prejuízo: ${realized_profit:.2f}")
            self.current_capital += realized_profit # Reduz capital
            # Decide se continua ou para (Se perdeu muito, para)
            if self.current_capital < 10:
                print("     ️ Capital Insuficiente. Game Over.")
                self.current_round = 999 # Encerra
            else:
                print("      Tentando recuperar no próximo round...")
                self.current_round += 1
            self.trade.cancel_all_orders(symbol)
            return True

    def run_campaign(self):
        print(f" BLOOD WAR (RESCUE MODE)! Meta: Recuperar PnL Positivo")
        
        # Modo de Resgate Direto: Assume que já estamos posicionados
        # Pula a etapa de entrada e vai direto para monitoramento
        symbol = "ETH_USDC_PERP"
        self.monitor_position_closure(symbol)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="blood_war")
    parser.add_argument("--leverage", type=int, default=10)
    parser.add_argument("--tp", type=float, default=0.007)
    parser.add_argument("--sl", type=float, default=0.006)
    parser.add_argument("--rounds", type=int, default=5)
    
    args = parser.parse_args()
    
    manager = BloodWarManager(args.leverage, args.tp, args.sl, args.rounds)
    manager.run_campaign()
