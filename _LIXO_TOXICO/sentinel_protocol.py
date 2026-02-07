#!/usr/bin/env python3
"""
️ Sentinel Protocol - Fortaleza de Contexto
Software de Moral Institucional para Gestão de Risco Automática
"""

import os
import time
import sys
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class SentinelProtocol:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        self.trade = BackpackTrade(self.auth)
        
        # Parâmetros da Fortaleza de Contexto (Modo Diamond Hand -> MODO GARANTIA)
        self.BREAKEVEN_TRIGGER = 0.004  # +0.4% PnL (Antes era 1.5%). Mal pagou a taxa, já protege.
        self.TRAILING_STEP = 0.003      # A cada 0.3% de lucro extra, sobe o stop
        self.FEE_BUFFER = 0.0012        # 0.12% para cobrir taxas
        self.MAX_SL_PCT = 0.06          # 6.0% Max Stop Loss (Catástrofe)
        
        print("️ Sentinel Protocol: OPERATIONAL_GREEN (Trailing Aggressive)")
        print(f"   Breakeven Trigger: +{self.BREAKEVEN_TRIGGER*100}%")
        print(f"   Trailing Step: +{self.TRAILING_STEP*100}%")
        
    def monitor(self):
        while True:
            try:
                # 1. Obter Posições Abertas
                positions = self.data.get_positions()
                
                # Filtrar apenas posições com tamanho > 0
                active_positions = [p for p in positions if float(p['quantity']) != 0]
                
                if not active_positions:
                    print(f" Nenhuma posição ativa. Scan em 30s...", end='\r')
                    time.sleep(30)
                    continue
                    
                print(f"\n Monitorando {len(active_positions)} posições ativas...")
                
                for pos in active_positions:
                    self.enforce_protocol(pos)
                    
                time.sleep(10) # Scan rápido
                
            except Exception as e:
                print(f" Erro no ciclo Sentinel: {e}")
                time.sleep(10)
                
    def enforce_protocol(self, pos):
        symbol = pos['symbol']
        side = pos['side'] # Long or Short
        entry_price = float(pos['entryPrice'])
        current_price = float(pos['markPrice'])
        quantity = abs(float(pos['quantity']))
        
        # Calcular PnL % (Variação de Preço)
        if side == "Long":
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
            
        print(f"    {symbol} ({side}): PnL {pnl_pct*100:.2f}% | Entry ${entry_price:.2f}")
        
        # 3.  RESGATE MET (FECHAR AGORA - UTI) - Removido (Não temos MET)
        
        # 4.  RESGATE SOL (REDUZIR EXPOSIÇÃO) - Removido (Operação Atual Saudável)
        
        # 1. Trailing Stop Dinâmico (Active Sniper Mode)
        # Se PnL > 1% e subindo, puxa o stop
        if pnl_pct >= 0.01:
             self.activate_trailing(symbol, side, entry_price, quantity, current_price, pnl_pct)

        # 2. Breakeven Guardian
        elif pnl_pct >= self.BREAKEVEN_TRIGGER:
            self.activate_breakeven(symbol, side, entry_price, quantity, current_price)
            
        # 3. Hard Floor Check (Verificar se existe SL)
        # self.verify_hard_floor(symbol, side, entry_price, quantity) # TODO: Implementar verificação de ordens abertas
        
    def activate_trailing(self, symbol, side, entry_price, quantity, current_price, pnl_pct):
        """Trailing Stop para garantir lucro maior"""
        # Se PnL é 1.5%, Stop vai para 1.0% (Lock 1%)
        lock_pct = pnl_pct - 0.005 # Deixa 0.5% de respiro
        if lock_pct < self.BREAKEVEN_TRIGGER: lock_pct = self.BREAKEVEN_TRIGGER
        
        if side == "Long":
            new_stop_price = entry_price * (1 + lock_pct)
        else:
            new_stop_price = entry_price * (1 - lock_pct)
            
        # Ajuste de precisão
        if "BONK" in symbol: new_stop_price = round(new_stop_price, 6)
        else: new_stop_price = round(new_stop_price, 2)
        
        print(f"    TRAILING STOP: {symbol} PnL {pnl_pct*100:.2f}% -> Stop @ ${new_stop_price}")
        
        # Cancelar stops antigos e criar novo
        try:
            self.trade.cancel_open_orders(symbol)
            # Enviar Stop Market
            # ... (Lógica de envio igual Breakeven)
            # Para simplificar, vamos reutilizar a lógica de envio do Breakeven ajustada
            self.send_stop_order(symbol, side, quantity, new_stop_price)
        except Exception as e:
            print(f"    Erro Trailing: {e}")

    def send_stop_order(self, symbol, side, quantity, stop_price):
         # Correção para BONK (Quantidade como string e inteira se for kBONK)
         qty_str = str(quantity)
         if "BONK" in symbol:
             qty_str = str(int(quantity))
             
         payload = {
            "symbol": symbol,
            "side": "Ask" if side == "Long" else "Bid",
            "orderType": "Market",
            "triggerPrice": str(stop_price),
            "quantity": qty_str,
            "reduceOnly": True
         }
         # Enviar via requests para garantir
         import requests
         headers = self.auth.get_headers(instruction="orderExecute", params=payload)
         requests.post("https://api.backpack.exchange/api/v1/order", headers=headers, json=payload)
         print(f"      Stop Atualizado para ${stop_price}")

    def activate_breakeven(self, symbol, side, entry_price, quantity, current_price):
        """Move o SL para Entry + Taxas"""
        print(f"    ATIVANDO BREAKEVEN GUARDIAN para {symbol}!")
        
        # Calcular novo preço de Stop (Entrada + Taxas)
        if side == "Long":
            new_stop_price = entry_price * (1 + self.FEE_BUFFER)
        else:
            new_stop_price = entry_price * (1 - self.FEE_BUFFER)
            
        # Ajuste de precisão
        if "BONK" in symbol: new_stop_price = round(new_stop_price, 6)
        else: new_stop_price = round(new_stop_price, 2)
        
        print(f"     ️ Stop Loss Ajustado para: ${new_stop_price}")
        
        # Executar Cancelamento + Nova Ordem
        try:
            self.trade.cancel_open_orders(symbol)
            time.sleep(1)
            self.send_stop_order(symbol, side, quantity, new_stop_price)
        except Exception as e:
            print(f"      Erro ao mover Stop: {e}")
            
if __name__ == "__main__":
    sentinel = SentinelProtocol()
    print("️ SENTINEL PROTOCOL INICIADO (Background Mode)...")
    sentinel.monitor()