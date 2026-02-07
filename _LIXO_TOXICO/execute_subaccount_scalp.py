import os
import sys
import time
import argparse
from dotenv import load_dotenv
sys.path.append('/Users/doublegreen/backpacktrading')
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# Load standard environment
load_dotenv()

class SubaccountScalper:
    def __init__(self, symbol="BTC_USDC_PERP", leverage=5, amount_usdc=20):
        self.symbol = symbol
        self.leverage = leverage
        self.amount_usdc = amount_usdc
        self.perp_key = None
        self.perp_secret = None
        
        # Load subaccount keys from file
        try:
            with open("DELTANEUTRO", "r") as f:
                lines = f.readlines()
                self.perp_key = lines[2].strip() 
                self.perp_secret = lines[7].strip()
                print(f"    Chave Subconta Carregada: {self.perp_key[:10]}...")
        except Exception as e:
            print(f"    Erro ao ler arquivo DELTANEUTRO: {e}")
            return

        self.auth = BackpackAuth(self.perp_key, self.perp_secret)
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
    def get_precision(self):
        filters = self.data.get_market_filters(self.symbol)
        price_tick = filters.get('tickSize', '0.1')
        qty_step = filters.get('stepSize', '0.001')
        return price_tick, qty_step

    def format_value(self, value, step):
        step_float = float(step)
        if step_float >= 1:
            return str(int(value))
        
        decimals = 0
        temp = step_float
        while temp < 1:
            temp *= 10
            decimals += 1
        return f"{value:.{decimals}f}"

    def execute(self):
        print(f"\n GHOST SCALPER (Subconta): {self.symbol}")
        print(f"   Modo: Operação Oculta na Carteira 2")
        
        # 1. Saldo Check
        balances = self.data.get_balances()
        available = float(balances.get('USDC', {}).get('available', 0))
        print(f"    Saldo Subconta: ${available:.2f}")
        
        # Lógica de 60% da Margem
        capital_to_use = available * 0.60
        
        if capital_to_use < 5:
            print(f"    Saldo insuficiente na Subconta (Min $5).")
            return

        print(f"   Margin: ${capital_to_use:.2f} (60%) | Leverage: {self.leverage}x")

        price_tick, qty_step = self.get_precision()
        
        # 2. Entrada (Market)
        ticker = self.data.get_ticker(self.symbol)
        price = float(ticker['lastPrice'])
        
        notional = capital_to_use * self.leverage
        qty = notional / price
        qty_str = self.format_value(qty, qty_step)
        
        print(f"    Entrada Subconta: {qty_str} {self.symbol}...")
        res = self.trade.execute_order(self.symbol, "Bid", None, qty_str, "Market")
        
        if not res:
            print("    Falha na entrada.")
            return
            
        print("    Entrada Confirmada! Monitorando...")
        time.sleep(2)
        
        # 3. Monitoramento Simples
        # Stop Loss: -2% Price
        # Take Profit: +3% Price
        
        entry_price = price
        sl_price = entry_price * 0.98
        tp_price = entry_price * 1.03
        
        print(f"   ️ SL: {sl_price:.2f} |  TP: {tp_price:.2f}")
        
        # Colocar TP Limit
        tp_str = self.format_value(tp_price, price_tick)
        self.trade.execute_order(self.symbol, "Ask", tp_str, qty_str, "Limit", reduce_only=True)
        
        # Colocar SL Market
        sl_str = self.format_value(sl_price, price_tick)
        self.trade.execute_order(self.symbol, "Ask", None, qty_str, "Market", trigger_price=sl_str, reduce_only=True)
        
        print("    Ordens de Saída posicionadas na Subconta.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="BTC_USDC_PERP")
    parser.add_argument("amount", nargs="?", default=20, type=float)
    args = parser.parse_args()
    
    bot = SubaccountScalper(symbol=args.symbol, amount_usdc=args.amount)
    bot.execute()
