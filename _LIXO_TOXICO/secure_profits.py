import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class ProfitGuardian:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.min_profit_pct = 0.002 # 0.2% para cobrir taxas e dar lucro mínimo

    def protect_positions(self):
        print("️ GUARDIÃO DE LUCROS (ZERO PERDAS)")
        print("===================================")
        
        positions = self.data.get_positions()
        if not positions:
            print("   Nenhuma posição ativa.")
            return

        for p in positions:
            symbol = p['symbol']
            qty = float(p.get('netQuantity', 0))
            if qty == 0: continue
            
            entry = float(p['entryPrice'])
            
            # Preço atual
            ticker = self.data.get_ticker(symbol)
            curr_price = float(ticker['lastPrice'])
            
            # PnL %
            roi = (curr_price - entry) / entry if qty > 0 else (entry - curr_price) / entry
            
            print(f"    {symbol}: ROI {roi*100:.2f}% (Entry: {entry} -> Curr: {curr_price})")
            
            # Lógica de Proteção
            # 1. Se ROI > 0.5% -> Mover Stop para Breakeven + 0.1%
            # 2. Se ROI > 1.0% -> Mover Stop para Entry + 0.5% (Trailing Manual)
            # 3. Se ROI > 3.0% -> Fechar (Take Profit de Emergência esticado)
            
            new_stop = None
            
            if roi > 0.03: # > 3.0% (Aumentado de 1.5% para 3.0% para deixar correr)
                print(f"       Lucro Extraordinário (>3.0%)! Fechando agora para garantir...")
                self.trade.close_position(symbol, qty)
                continue
                
            elif roi > 0.01: # > 1.0%
                print(f"       Lucro Bom (>1.0%). Subindo Stop para garantir 0.5%...")
                # Stop em Entry + 0.5%
                if qty > 0: new_stop = entry * 1.005
                else: new_stop = entry * 0.995
                
            elif roi > 0.003: # > 0.3% (Já cobre taxas)
                print(f"      ️ Lucro Mínimo (>0.3%). Movendo para Breakeven...")
                # Stop em Entry + 0.1% (Para pagar taxas)
                if qty > 0: new_stop = entry * 1.001
                else: new_stop = entry * 0.999
            
            # Aplicar Novo Stop se definido
            if new_stop:
                # Cancelar stops antigos
                self.trade.cancel_open_orders(symbol)
                time.sleep(1)
                
                # Colocar novo Stop Market
                side = "Ask" if qty > 0 else "Bid"
                trigger = f"{new_stop:.2f}"
                if symbol == "BTC_USDC_PERP": trigger = f"{new_stop:.1f}" # Precisão BTC
                
                print(f"       Ajustando Stop para {trigger}...")
                # Tentar Market Trigger se StopMarket falhar (Backpack API quirk)
                # Na verdade, o erro é "OrderTypeEnum", found "StopMarket".
                # A API pode esperar "Market" com "triggerPrice".
                
                res = self.trade.execute_order(
                    symbol, 
                    side, 
                    None, 
                    str(abs(qty)), 
                    order_type="Market", # Trocando para Market com Trigger
                    trigger_price=trigger, 
                    reduce_only=True
                )
                if res:
                     print(f"       Stop Protegido em {trigger}")

if __name__ == "__main__":
    bot = ProfitGuardian()
    while True:
        try:
            bot.protect_positions()
        except Exception as e:
            print(f"Erro: {e}")
        time.sleep(10)
