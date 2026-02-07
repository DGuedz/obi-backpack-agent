import time
import os
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

def supreme_sentinel():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    trade = BackpackTrade(auth)
    
    print("️ SENTINELA SUPREMO: VIGILÂNCIA ATIVA (IRONCLAD MODE)")
    print("Regra 1: Posição sem Stop Loss = MORTE IMEDIATA")
    
    while True:
        try:
            # 1. Pega posições
            positions = data.get_positions()
            open_orders = data.get_open_orders()
            
            for pos in positions:
                symbol = pos['symbol']
                qty = float(pos.get('quantity', pos.get('netQuantity', 0)))
                
                if qty == 0: continue
                
                # Verifica se existe ALGUMA ordem aberta para este símbolo (Suposição de que é o SL/TP)
                has_protection = False
                for order in open_orders:
                    if order['symbol'] == symbol:
                        # Na API Backpack, Trigger Orders (Stop Loss) aparecem aqui
                        # Podemos refinar checando se é trigger order, mas por enquanto, qualquer ordem conta como tentativa de proteção
                        # Idealmente, checar se side é oposto à posição
                        has_protection = True
                        break
                
                if not has_protection:
                    print(f" ALERTA CRÍTICO: {symbol} ESTÁ DESPROTEGIDO (SEM STOP LOSS NO BOOK)!")
                    
                    # TENTATIVA DE RECUPERAÇÃO ANTES DO PÂNICO
                    # Tentar colocar Stop Loss de Emergência (1%)
                    print(f"   ️ Tentando Inserir Stop Loss de Emergência (1%)...")
                    ticker = data.get_ticker(symbol)
                    current_price = float(ticker['lastPrice'])
                    
                    if qty > 0: # Long -> Sell Stop
                        sl_price = current_price * 0.99
                        side = "Ask"
                    else: # Short -> Buy Stop
                        sl_price = current_price * 1.01
                        side = "Bid"
                        
                    try:
                        # Tentar enviar Stop Market
                        trade.execute_order(
                            symbol=symbol,
                            side=side,
                            order_type="StopMarket",
                            quantity=abs(qty),
                            trigger_price=sl_price
                        )
                        print(f"    Stop Loss de Emergência inserido em {sl_price}!")
                        continue # Salvo pelo gongo
                    except Exception as e:
                        print(f"    Falha ao inserir Stop de Emergência: {e}")
                    
                    # SE FALHAR, PÂNICO TOTAL
                    print(f" EXECUTANDO FECHAMENTO DE EMERGÊNCIA (MARKET CLOSE) EM {symbol}...")
                    
                    # Fecha a mercado para salvar o capital restante
                    close_side = "Ask" if qty > 0 else "Bid"
                    trade.execute_order(symbol, close_side, 0, abs(qty), order_type="Market")
                    print(f" Posição {symbol} encerrada pelo Sentinela.")
                
            time.sleep(3) # Varredura rápida
            
        except Exception as e:
            print(f"Erro no loop do Sentinela: {e}")
            time.sleep(5)

if __name__ == "__main__":
    supreme_sentinel()
