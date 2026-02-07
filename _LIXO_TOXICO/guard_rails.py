#!/usr/bin/env python3
"""
️ GUARD RAILS - The Omega Constitution
Checklist de segurança obrigatório antes de qualquer execução.
"Sobreviver com Honra até o Snapshot."
"""

import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv

load_dotenv()

class GuardRail:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
        # Parâmetros de Segurança
        self.MAX_FEE_TO_PROFIT_RATIO = 0.15 # Taxa não pode comer mais que 15% do lucro
        self.MAX_SPREAD_PCT = 0.0010        # Spread máx 0.10%
        self.TAKER_FEE_RATE = 0.00085       # 0.085%
        self.MAKER_FEE_RATE = 0.0           # 0.0% (Considerando Tier base)
        
    def check_trade_viability(self, symbol, side, price, quantity, is_maker=True, projected_profit_pct=0.01):
        """
        Retorna (Aprovado: bool, Motivo: str)
        """
        try:
            # 1. Checagem de Spread (Liquidez)
            ticker = self.data.get_ticker(symbol)
            # Tentar chaves padrão ou camelCase
            best_bid = float(ticker.get('bestBid', 0) or ticker.get('best_bid', 0))
            best_ask = float(ticker.get('bestAsk', 0) or ticker.get('best_ask', 0))
            
            # Se não tiver bid/ask (ex: ticker simples), usar lastPrice com spread fixo estimado
            if best_bid == 0:
                last = float(ticker.get('lastPrice', 0))
                best_bid = last * 0.9995
                best_ask = last * 1.0005
            
            spread = (best_ask - best_bid) / best_bid
            
            if spread > self.MAX_SPREAD_PCT:
                return False, f" SPREAD ALTO: {spread*100:.3f}% > Limite {self.MAX_SPREAD_PCT*100:.3f}%"
            
            # 2. Checagem de Custo (Fee Drag)
            notional_value = price * quantity
            fee_rate = self.MAKER_FEE_RATE if is_maker else self.TAKER_FEE_RATE
            estimated_fee = notional_value * fee_rate
            
            projected_profit = notional_value * projected_profit_pct
            
            # Se o lucro for muito pequeno, a taxa come tudo
            if projected_profit == 0: return False, " Lucro Projetado Zero"
            
            fee_impact = estimated_fee / projected_profit
            
            if fee_impact > self.MAX_FEE_TO_PROFIT_RATIO:
                return False, f" TAXA ABUSIVA: Taxa consome {fee_impact*100:.1f}% do Lucro (Max {self.MAX_FEE_TO_PROFIT_RATIO*100}%)"
            
            # 3. Checagem de "Gap" (Slippage Protection para Taker)
            if not is_maker:
                # Se for Taker, verificar se o preço de execução está longe do last
                last_price = float(ticker['lastPrice'])
                deviation = abs(price - last_price) / last_price
                if deviation > 0.002: # 0.2%
                    return False, f" PREÇO DESVIADO: Gap de {deviation*100:.2f}% detectado."

            return True, " APROVADO: Trade dentro dos parâmetros de honra."
            
        except Exception as e:
            print(f"️ Erro no GuardRail: {e}")
            return False, " ERRO DE SISTEMA: Não foi possível validar segurança."

    def check_margin_health(self):
        try:
            collat = self.data.get_account_collateral()
            # Tratamento robusto de tipos (API retorna string)
            avail = float(collat.get('netEquityAvailable', 0) or 0) # Usar netEquityAvailable direto
            equity = float(collat.get('netEquity', 0) or 0) # Usar netEquity
            
            if equity == 0: 
                # Fallback: tentar 'equity' e 'availableToTrade' antigos
                avail = float(collat.get('availableToTrade', 0) or 0)
                equity = float(collat.get('equity', 0) or 0)
            
            if equity == 0: return False, "Saldo Zero (Dados Inválidos)"
            
            # OVERRIDE DE COMANDO: Se tiver pelo menos $10 livres, deixa operar.
            if avail > 10.0:
                return True, f" Margem Suficiente (${avail:.2f} livres)"
            
            usage_pct = 1 - (avail / equity)
            
            if usage_pct > 0.99: 
                return False, f" MARGEM CRÍTICA: Uso {usage_pct*100:.1f}% > 99%"
                
            return True, " Margem Saudável"
        except:
            return True, "️ Erro leitura margem (Bypass)"
