import os
import sys
import time
import argparse
from dotenv import load_dotenv
sys.path.append('/Users/doublegreen/backpacktrading')
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

load_dotenv()

class Sniper20x:
    def __init__(self, symbol="BTC_USDC_PERP", amount_usdc=20):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        self.symbol = symbol
        self.leverage = 20
        self.amount_usdc = amount_usdc
        
    def get_precision(self):
        filters = self.data.get_market_filters(self.symbol)
        price_tick = filters.get('tickSize', '0.0001')
        qty_step = filters.get('stepSize', '1.0')
        return price_tick, qty_step

    def format_value(self, value, step):
        step_float = float(step)
        
        # Round to nearest step
        if step_float > 0:
            value = round(value / step_float) * step_float
        
        # Format decimal places
        if step_float >= 1:
            return str(int(value))
        
        decimals = 0
        temp = step_float
        while temp < 1:
            temp *= 10
            decimals += 1
        return f"{value:.{decimals}f}"

    def execute(self):
        print(f"\n SNIPER 20x: {self.symbol}")
        print(f"   Modo: Alta Voltagem (Scalp Rápido)")
        
        # 0. Check Existing Position FIRST
        positions = self.data.get_positions()
        existing_pos = next((p for p in positions if p['symbol'] == self.symbol), None)
        price_tick, qty_step = self.get_precision()
        
        if existing_pos and float(existing_pos['netQuantity']) != 0:
            print(f"   ️ Posição Existente Detectada!")
            entry_price = float(existing_pos['entryPrice'])
            qty = float(existing_pos['netQuantity'])
            print(f"    Entry: ${entry_price} | Qty: {qty}")
            print("   ⏩ Pulando entrada e indo direto para Monitoramento...")
            qty_str = self.format_value(abs(qty), qty_step)
        else:
            # 1. Saldo Check
            balances = self.data.get_balances()
            available = float(balances.get('USDC', {}).get('available', 0))
            
            capital_to_use = 0
            if isinstance(self.amount_usdc, str) and '%' in self.amount_usdc:
                pct = float(self.amount_usdc.replace('%', '')) / 100
                capital_to_use = available * pct
                print(f"   Allocation: {pct*100}% of ${available:.2f} => ${capital_to_use:.2f}")
            else:
                capital_to_use = float(self.amount_usdc)
                if capital_to_use > available:
                     print(f"   ️ Capital solicitado (${capital_to_use}) > Disponível. Ajustando para 95% do saldo.")
                     capital_to_use = available * 0.95
            
            if capital_to_use < 5:
                print(f"    Saldo Insuficiente (<$5): ${available:.2f}")
                return

            print(f"   Margin: ${capital_to_use:.2f} | Leverage: {self.leverage}x | Notional: ${capital_to_use * self.leverage:.2f}")

            # 2. Entrada (Market)
            ticker = self.data.get_ticker(self.symbol)
            price = float(ticker['lastPrice'])
            
            # Reduzir Notional drasticamente porque a API pode estar exigindo mais margem inicial para altcoins voláteis em 20x
            notional = capital_to_use * self.leverage * 0.50 # 50% buffer
            qty = notional / price
            qty_str = self.format_value(qty, qty_step)
            
            print(f"    Executando Entrada a Mercado: {qty_str} {self.symbol}...")
            res = self.trade.execute_order(self.symbol, "Bid", None, qty_str, "Market")
            
            if not res:
                print("    Falha na entrada.")
                return
                
            print("    Entrada Confirmada! Iniciando Monitoramento Assistido...")
            time.sleep(2)
            
            # Re-fetch position to get exact entry
            positions = self.data.get_positions()
            existing_pos = next((p for p in positions if p['symbol'] == self.symbol), None)
            if existing_pos:
                entry_price = float(existing_pos['entryPrice'])
            else:
                entry_price = price # Fallback

        # 3. Monitoramento Ativo (Frontend Assist)
        print(f"    Entry Real: ${entry_price}")
        
        # Stops Iniciais (Mental/Script)
        # FOGO is Volatile. 20x Leverage.
        # Stop Loss: -1.0% Price (-20% ROE) -> More room to breathe for FOGO
        # Take Profit: +2.0% Price (+40% ROE)
        
        sl_pct = 0.01
        tp_pct = 0.02
        
        sl_price = entry_price * (1 - sl_pct)
        tp_price = entry_price * (1 + tp_pct)
        
        print(f"   ️ Stop Loss: ${sl_price:.4f} (-20%)")
        print(f"    Take Profit: ${tp_price:.4f} (+40%)")
        
        # Loop Visual
        max_roe = -999
        
        try:
            while True:
                ticker = self.data.get_ticker(self.symbol)
                curr_price = float(ticker['lastPrice'])
                
                roe = (curr_price - entry_price) / entry_price * 100 * self.leverage
                if roe > max_roe: max_roe = roe
                
                # Visual Bar
                # Range -20% to +20%
                bar_len = 20
                pos_norm = int((roe + 20) / 40 * bar_len)
                pos_norm = max(0, min(bar_len, pos_norm))
                bar = ['-'] * bar_len
                if 0 <= pos_norm < bar_len:
                    bar[pos_norm] = '█'
                bar_str = "".join(bar)
                
                color = "🟢" if roe > 0 else ""
                print(f"   {color} ROE: {roe:6.2f}% | Price: {curr_price:.4f} | Max: {max_roe:6.2f}% [{bar_str}]", end='\r')
                
                # Lógica de Saída
                if roe <= -20:
                    print(f"\n    STOP LOSS ATINGIDO! Fechando...")
                    self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market")
                    break
                    
                if roe >= 40:
                    print(f"\n    TAKE PROFIT ATINGIDO! Fechando...")
                    self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market")
                    break
                    
                # Trailing Stop Simples
                # Se bater +15%, Stop vai para Breakeven
                if max_roe > 15 and roe < 2:
                    print(f"\n   ️ TRAILING STOP (Breakeven) acionado! Saindo no lucro/zero.")
                    self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market")
                    break
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n    Controle Manual: Encerrar Posição? (y/n)")
            # Simulação de interação
            print("   Encerrando por segurança...")
            self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="BTC_USDC_PERP")
    parser.add_argument("amount", nargs="?", default="20") # Default string to allow %
    args = parser.parse_args()
    
    bot = Sniper20x(symbol=args.symbol, amount_usdc=args.amount)
    bot.execute()
