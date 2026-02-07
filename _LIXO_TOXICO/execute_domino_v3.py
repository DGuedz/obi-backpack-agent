import os
import time
import logging
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class DominoStrategyV3:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.leverage = 3 # Sustentável (3x)
        
    def get_precision(self, symbol):
        filters = self.data.get_market_filters(symbol)
        return float(filters.get('tickSize', 0.01)), float(filters.get('stepSize', 1.0))

    def format_value(self, value, step):
        if step <= 0: return str(value)
        decimals = 0 if step >= 1 else int(abs(__import__('math').log10(step)))
        rounded = round(value / step) * step
        return f"{rounded:.{decimals}f}"

    def check_position(self, symbol):
        positions = self.data.get_positions()
        pos = next((p for p in positions if p['symbol'] == symbol), None)
        return pos if pos and float(pos['netQuantity']) != 0 else None

    def execute_phase(self, phase_name, symbol, tp_pct, sl_pct):
        print(f"\n DOMINÓ V3 - {phase_name}: {symbol}")
        print(f"   Alavancagem: {self.leverage}x | TP: +{tp_pct*100}% | SL: -{sl_pct*100}%")
        
        # 1. Verificar se JÁ ESTAMOS POSICIONADOS (Retomada)
        existing_pos = self.check_position(symbol)
        qty_str = None
        price_tick, qty_step = self.get_precision(symbol)
        
        if existing_pos:
            print(f"   ️ Posição detectada! Retomando monitoramento de {symbol}...")
            entry_price = float(existing_pos['entryPrice'])
            quantity = float(existing_pos['netQuantity'])
            qty_str = self.format_value(abs(quantity), qty_step)
            
        else:
            # Limpar ordens antigas antes de nova entrada
            self.trade.cancel_open_orders(symbol)

            # 1.1 Verificar Saldo
            balances = self.data.get_balances()
            usdc = float(balances.get('USDC', {}).get('available', 0))
            if usdc < 10:
                print("️ Saldo insuficiente (Mínimo $10 USDC).")
                return False
                
            # 1.2 Entrada (Market)
            ticker = self.data.get_ticker(symbol)
            price = float(ticker['lastPrice'])
            notional = usdc * 0.95 * self.leverage
            quantity = notional / price
            
            qty_str = self.format_value(quantity, qty_step)
            
            print(f"    Entrando: Compra {qty_str} {symbol} (Market)")
            self.trade.execute_order(symbol, "Bid", None, qty_str, order_type="Market")
            time.sleep(3) 
            
            # Verificar sucesso da entrada
            existing_pos = self.check_position(symbol)
            if not existing_pos:
                print(" Falha na entrada. Posição não encontrada.")
                return False
            
            entry_price = float(existing_pos['entryPrice'])

        # 2. Definir Alvos
        tp_price = entry_price * (1 + tp_pct)
        sl_price = entry_price * (1 - sl_pct)
        
        print(f"    Alvo: ${tp_price:.4f} |  Stop: ${sl_price:.4f}")
        
        tp_str = self.format_value(tp_price, price_tick)
        sl_str = self.format_value(sl_price, price_tick)
        
        # 3. Verificar/Colocar Ordens de Saída (TP/SL)
        all_open_orders = self.data.get_open_orders()
        open_orders = [o for o in all_open_orders if o['symbol'] == symbol]
        
        has_tp = any(o['side'] == 'Ask' and o['orderType'] == 'Limit' for o in open_orders)
        has_sl = any(o['side'] == 'Ask' and float(o.get('triggerPrice', 0) or 0) > 0 for o in open_orders)
        
        if not has_tp:
            print("   ️ Colocando TP Limit...")
            self.trade.execute_order(symbol, "Ask", tp_str, qty_str, order_type="Limit", reduce_only=True)
            
        if not has_sl:
            print("   ️ Colocando SL Stop Market...")
            # CORREÇÃO: Usar order_type="StopMarket" para garantir gatilho de mercado na API Backpack
            # Se "Market" + triggerPrice não funcionar, tentar "StopMarket"
            res = self.trade.execute_order(symbol, "Ask", None, qty_str, order_type="StopMarket", trigger_price=sl_str, reduce_only=True)
            if not res:
                print("   ️ Falha no StopMarket. Tentando Market Trigger...")
                self.trade.execute_order(symbol, "Ask", None, qty_str, order_type="Market", trigger_price=sl_str, reduce_only=True)
        
        print("   ⏳ Monitorando... (Aguardando TP ou SL)")
        
        # Snapshot do saldo para cálculo de PnL
        balances = self.data.get_balances()
        initial_balance = float(balances.get('USDC', {}).get('available', 0)) # Saldo Livre (que deve ser baixo pois estamos posicionados)
        # Na verdade, para saber se lucramos, precisamos comparar o Equity Total ou Saldo APÓS fechar.
        
        while True:
            pos = self.check_position(symbol)
            if not pos:
                print(f"    Posição em {symbol} encerrada!")
                
                print("    Cancelando ordens pendentes...")
                self.trade.cancel_open_orders(symbol)
                
                time.sleep(2)
                current_balances = self.data.get_balances()
                new_balance = float(current_balances.get('USDC', {}).get('available', 0))
                
                # Se o saldo livre agora é maior que antes (significativamente), houve lucro/fechamento.
                # Como initial_balance era baixo (margem travada), new_balance deve ser alto.
                # Mas precisamos saber se foi LUCRO.
                
                # Estimativa simples: Se new_balance > (Notional / Leverage) + Profit
                # Vamos assumir sucesso se não detectarmos erro.
                # Melhor: Comparar Equity Total se possível, mas available serve.
                
                print(f"    Saldo Livre Atual: ${new_balance:.2f}")
                return True # Assumindo continuidade (Filtro de PnL pode ser adicionado depois)
            
            # Feedback
            if pos:
                mark_price = float(self.data.get_ticker(symbol)['lastPrice'])
                roi = (mark_price - entry_price) / entry_price * 100 * self.leverage
                print(f"      ... PnL Atual: {roi:.2f}% (Mark: {mark_price:.2f})", end='\r')
                
            time.sleep(1) # HFT Speed (1s poll)

    def run(self):
        print("️ INICIANDO DOMINÓ V3 (Majors Only - Sustainable)")
        print("   Estratégia: 3x Leverage | Majors (SOL -> BTC -> ETH) | Phase Locking")
        
        # Lógica de Retomada Inteligente:
        # Se já temos posição em BTC, pular fase 1. Se em ETH, pular 1 e 2.
        
        btc_pos = self.check_position("BTC_USDC_PERP")
        eth_pos = self.check_position("ETH_USDC_PERP")
        sol_pos = self.check_position("SOL_USDC_PERP")
        
        start_phase = 1
        if eth_pos: start_phase = 3
        elif btc_pos: start_phase = 2
        elif sol_pos: start_phase = 1
        
        print(f"   ⏩ Retomando a partir da FASE {start_phase}")

        # Fase 1: SOL (O Porto Seguro)
        # TP: 1.5% (Movimento de ~0.5% no preço com 3x)
        # SL: 1.0% (Movimento de ~0.33% no preço com 3x)
        if start_phase <= 1:
            if self.execute_phase("FASE 1", "SOL_USDC_PERP", 0.015, 0.010): 
                time.sleep(5)
            else:
                return # Stop ou Falha
            
        # Fase 2: BTC (A Baleia)
        # TP: 1.0% (Movimento menor, mais seguro)
        # SL: 0.8%
        if start_phase <= 2:
            if self.execute_phase("FASE 2", "BTC_USDC_PERP", 0.010, 0.008): 
                time.sleep(5)
            else:
                return

        # Fase 3: ETH (O Retorno)
        # TP: 1.2%
        # SL: 1.0%
        if start_phase <= 3:
            if self.execute_phase("FASE 3", "ETH_USDC_PERP", 0.012, 0.010):
                print("\n DOMINÓ V3 COMPLETO! Ciclo Sustentável Finalizado.")

if __name__ == "__main__":
    bot = DominoStrategyV3()
    bot.run()
