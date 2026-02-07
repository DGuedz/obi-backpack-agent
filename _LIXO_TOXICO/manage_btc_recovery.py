import os
import sys
import time
from dotenv import load_dotenv
sys.path.append('/Users/doublegreen/backpacktrading')
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

class BTCRecoveryManager:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.symbol = "BTC_USDC_PERP"
        self.leverage = 3
        
    def get_precision(self):
        filters = self.data.get_market_filters(self.symbol)
        price_tick = filters.get('tickSize', '0.1')
        qty_step = filters.get('stepSize', '0.0001')
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
        print(f"\n BTC RECOVERY MANAGER: {self.symbol}")
        print("   Objetivo: Resgate de Posição (Breakeven ou Pequeno Lucro)")
        
        # 1. Check Position
        positions = self.data.get_positions()
        pos = next((p for p in positions if p['symbol'] == self.symbol), None)
        
        if not pos:
            print("    Nenhuma posição de BTC ativa. Nada a resgatar.")
            return

        entry_price = float(pos['entryPrice'])
        qty = float(pos['netQuantity'])
        
        if qty == 0:
            print("   ️ Quantidade zerada (Fantasma?). Sair.")
            return
            
        print(f"    Posição Detectada: {qty} BTC @ ${entry_price:.2f}")
        
        # 2. Setup Recovery Orders
        # TP: Entry + 0.5% (Cobrir taxas e sair)
        # SL: Entry - 1.2% (Stop Técnico de Emergência)
        
        tp_price = entry_price * 1.005
        sl_price = entry_price * 0.988 # 1.2% Risk
        
        price_tick, qty_step = self.get_precision()
        
        tp_str = self.format_value(tp_price, price_tick)
        sl_str = self.format_value(sl_price, price_tick)
        qty_str = self.format_value(abs(qty), qty_step)
        
        print(f"    Alvo (TP): ${tp_str} (+0.5%)")
        print(f"   ️ Stop (SL): ${sl_str} (-1.2%)")
        
        # 3. Place Orders (Refresh)
        print("   ️ Atualizando ordens de proteção...")
        self.trade.cancel_open_orders(self.symbol)
        time.sleep(1)
        
        # TP Limit
        self.trade.execute_order(self.symbol, "Ask", tp_str, qty_str, "Limit", reduce_only=True)
        
        # SL Stop Market (Trigger)
        self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market", trigger_price=sl_str, reduce_only=True)
        
        print("    Proteções Ativas! Monitorando PnL...")
        
        while True:
            try:
                ticker = self.data.get_ticker(self.symbol)
                curr_price = float(ticker['lastPrice'])
                roi = (curr_price - entry_price) / entry_price * 100 * self.leverage
                
                print(f"   BTC Price: ${curr_price:.2f} | PnL: {roi:.2f}% | Target: ${tp_str}", end='\r')
                
                # Check exit
                pos_check = self.data.get_positions()
                still_open = any(p['symbol'] == self.symbol and float(p['netQuantity']) != 0 for p in pos_check)
                if not still_open:
                    print(f"\n    Posição BTC encerrada!")
                    break
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n    Monitoramento pausado.")
                break
            except Exception as e:
                print(f"\n   ️ Erro: {e}")
                time.sleep(5)

if __name__ == "__main__":
    manager = BTCRecoveryManager()
    manager.execute()
