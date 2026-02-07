import os
import sys
import time
import argparse
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

sys.path.append('/Users/doublegreen/backpacktrading')
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

class FireScalpExecutor:
    def __init__(self, symbol="SOL_USDC_PERP", leverage=3):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.symbol = symbol
        self.leverage = leverage
        
    def get_precision(self, symbol):
        filters = self.data.get_market_filters(symbol)
        price_tick = filters.get('tickSize', '0.01')
        qty_step = filters.get('stepSize', '0.1')
        return price_tick, qty_step

    def format_value(self, value, step):
        step_float = float(step)
        if step_float < 1:
            decimals = 0
            temp = step_float
            while temp < 1:
                temp *= 10
                decimals += 1
            return f"{value:.{decimals}f}"
        else:
            return f"{int(value)}"

    def execute(self):
        print(f"\n FIRE SCALP EXECUTOR: {self.symbol}")
        print(f"   Estratégia: 'Free Ride' (Entrada Sniper -> Breakeven -> Surf)")
        print(f"   Meta Inicial: 5% ROE | Alavancagem: {self.leverage}x")
        
        # 1. Check Balance
        balances = self.data.get_balances()
        usdc = float(balances.get('USDC', {}).get('available', 0))
        print(f"    Saldo Disponível: ${usdc:.2f}")
        
        if usdc < 5:
            print("    Saldo insuficiente para operar (< $5).")
            return
            
        # 2. Check Existing Position
        positions = self.data.get_positions()
        existing = next((p for p in positions if p['symbol'] == self.symbol), None)
        price_tick, qty_step = self.get_precision(self.symbol)
        
        if existing:
            print(f"   ️ Já existe posição aberta em {self.symbol}!")
            entry_price = float(existing['entryPrice'])
            pnl = existing.get('pnl', existing.get('unrealizedPnl', 'N/A'))
            print(f"      Entry: {entry_price} | PnL: {pnl}")
            # Se já existe, pulamos para o monitoramento
        else:
            # 3. Calculate Entry
            ticker = self.data.get_ticker(self.symbol)
            price = float(ticker['lastPrice'])
            notional = usdc * 0.95 * self.leverage # Use 95% of balance
            quantity = notional / price
            
            qty_str = self.format_value(quantity, qty_step)
            
            print(f"    Entrada: Market Buy {qty_str} {self.symbol} @ ~${price}")
            
            # 4. Execute Buy
            res = self.trade.execute_order(self.symbol, "Bid", None, qty_str, "Market")
            if not res:
                print("    Falha na execução da ordem de entrada.")
                return
                
            print("    Ordem enviada! Aguardando confirmação...")
            time.sleep(2)
            
            # Confirm
            positions = self.data.get_positions()
            existing = next((p for p in positions if p['symbol'] == self.symbol), None)
            if not existing:
                print("    Posição não encontrada após execução.")
                return
            entry_price = float(existing['entryPrice'])

        # --- MONITORAMENTO ATIVO (SURF) ---
        print("\n INICIANDO MODO SURF (Monitoramento Ativo)...")
        print("   Regras:")
        print("   1. Stop Inicial: -1.5% (Proteção de Capital)")
        print("   2. Breakeven: Ao atingir +1.5% ROE")
        print("   3. Take Profit Parcial: Ao atingir +5% ROE (Tirar Risco)")
        print("   4. Surf: Deixar o resto correr com Trailing Stop")
        
        # Definir Stop Inicial Hard (se não houver)
        sl_price_init = entry_price * (1 - 0.005) # 0.5% price move = 1.5% ROE at 3x
        sl_str = self.format_value(sl_price_init, price_tick)
        
        # TODO: Implementar lógica de verificação de ordens abertas e colocar SL se não existir
        # Por simplicidade, vamos monitorar via script e fechar a mercado se bater.
        # Mas para segurança, deveríamos ter um Stop na exchange.
        
        real_qty = float(existing['netQuantity'])
        qty_str = self.format_value(abs(real_qty), qty_step)
        
        # Colocar Stop Loss Inicial na Exchange
        print(f"   ️ Colocando Stop Loss Inicial em ${sl_str}...")
        self.trade.cancel_open_orders(self.symbol) # Limpar anteriores
        # Backpack uses "Market" with triggerPrice for Stop Market
        self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market", trigger_price=sl_str)
        
        breakeven_activated = False
        tp_activated = False
        
        while True:
            try:
                ticker = self.data.get_ticker(self.symbol)
                current_price = float(ticker['lastPrice'])
                
                roe = (current_price - entry_price) / entry_price * 100 * self.leverage
                
                print(f"   Price: ${current_price:.4f} | ROE: {roe:.2f}% | BE: {'' if breakeven_activated else ''} | TP: {'' if tp_activated else ''}", end='\r')
                
                # 1. Ativar Breakeven (+1.5% ROE)
                if roe > 1.5 and not breakeven_activated:
                    be_price = entry_price * 1.001 # Levemente acima para cobrir taxas
                    be_str = self.format_value(be_price, price_tick)
                    print(f"\n    ATIVANDO BREAKEVEN! Movendo Stop para ${be_str}")
                    self.trade.cancel_open_orders(self.symbol)
                    self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market", trigger_price=be_str)
                    breakeven_activated = True
                    
                # 2. Take Profit Parcial (+5% ROE)
                if roe > 5.0 and not tp_activated:
                    print(f"\n    ALVO ATINGIDO (+5%)! Realizando Parcial (75%)...")
                    # Vender 75%
                    qty_sell = abs(real_qty) * 0.75
                    qty_sell_str = self.format_value(qty_sell, qty_step)
                    
                    self.trade.execute_order(self.symbol, "Ask", None, qty_sell_str, "Market")
                    tp_activated = True
                    
                    # Atualizar quantidade restante para o Stop
                    remaining_qty = abs(real_qty) - float(qty_sell_str) # Aprox
                    qty_str = self.format_value(remaining_qty, qty_step)
                    
                    # Mover Stop do restante para +3% (Garantir lucro no Surf)
                    new_sl = entry_price * (1 + 0.01) # +1% Price = +3% ROE
                    new_sl_str = self.format_value(new_sl, price_tick)
                    print(f"    SURF MODE: Stop do restante ajustado para ${new_sl_str}")
                    
                    self.trade.cancel_open_orders(self.symbol)
                    self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market", trigger_price=new_sl_str)
                    
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n    Monitoramento interrompido pelo usuário.")
                break
            except Exception as e:
                print(f"\n   ️ Erro no loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="SOL_USDC_PERP")
    args = parser.parse_args()
    
    executor = FireScalpExecutor(symbol=args.symbol)
    executor.execute()
