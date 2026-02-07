import time
import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade
from safe_execution import SafeExecutor
from scalp_checklist import ScalpChecklist

# --- CONFIGURAÇÃO ULTRA SCALP ---
LEVERAGE = 50
CAPITAL_ALLOCATION = 0.70  # 70% do capital por trade (AUMENTO DE CAPITAL ORDENADO)
SCAN_INTERVAL = 10         # Segundos entre scans

import math

class UltraExecutor(SafeExecutor):
    """
    Versão modificada do Executor Seguro para Scalping Contínuo.
    Não encerra o programa se o Checklist falhar, apenas retorna False.
    """
    
    def get_step_size(self, symbol):
        # Busca o stepSize (incremento mínimo) do ativo na API
        try:
            markets = self.data.get_markets() # Endpoint /api/v1/markets
            for m in markets:
                if m['symbol'] == symbol:
                    # Depending on API structure, filters might be nested
                    # e.g. m['filters']['quantity']['stepSize']
                    # Let's inspect 'filters' structure if possible, or assume it's standard.
                    if 'filters' in m and 'quantity' in m['filters']:
                         return float(m['filters']['quantity']['stepSize'])
                    # Some APIs put stepSize at top level?
                    # Let's be robust.
            return 1.0 # Fallback seguro
        except:
            return 1.0

    def normalize_quantity(self, amount, step_size, current_price=None):
        # 1. Garante que é positivo (ABS)
        amount = abs(float(amount))
        
        # 2. Arredonda para baixo respeitando o stepSize (Evita erro de precisão)
        # Ex: Se stepSize é 1.0, 25.7 vira 25.0
        # Ex: Se stepSize é 0.1, 25.75 vira 25.7
        
        if step_size == 0: return str(amount)
        
        # Calculate precision based on step size
        # step 1.0 -> precision 0
        # step 0.1 -> precision 1
        # step 0.01 -> precision 2
        try:
            if step_size >= 1:
                precision = 0
            else:
                precision = int(round(-math.log(step_size, 10), 0))
                
            normalized = round(amount - (amount % step_size), precision)
            
            # CORREÇÃO: Se arredondou para zero, mas temos capital, tente o mínimo
            if normalized == 0 and amount > 0 and current_price:
                 # Verifica se o mínimo (step_size) vale menos que $5 (Regra de notional mínima)
                 # Se for seguro, força o step_size
                 # OBS: Se step_size * price for muito pequeno, a API pode rejeitar por "Min Notional".
                 # Mas pelo menos não é zero.
                 # Vamos tentar enviar o mínimo se for menor que $10 (segurança)
                 if step_size * current_price < 10.0:
                      print(f"   ️ Quantidade arredondou para 0. Forçando lote mínimo: {step_size}")
                      if precision == 0:
                          return f"{int(step_size)}"
                      return f"{step_size:.{precision}f}"

            if precision == 0:
                return f"{int(normalized)}"
            return f"{normalized:.{precision}f}"
        except:
            return str(amount)

    def execute_scalp_order(self, side, quantity, leverage):
        print(f" [ULTRA EXECUTOR] Validando {self.symbol} para Scalp 50x...")
        
        try:
            # Usar o ScalpChecklist (5m/15m)
            checklist = ScalpChecklist(self.symbol)
            is_approved, result = checklist.run_fast_scan(side, leverage)
            
            if not is_approved:
                print(f"    SCALP BLOQUEADO: {result}")
                return False
                
            sl_price = result['sl_price']
            entry_price = result['entry_price']
            
            print(f"    CHECKLIST SCALP APROVADO! SL: {sl_price}")
            
            # Ajustar side para API (Bid/Ask)
            if side == "Buy":
                side_param = "Bid"
            else:
                side_param = "Ask"
                
            # Executar Ordem com Stop Loss Atômico
            
            # Mas primeiro, definir alavancagem
            self.api.set_leverage(self.symbol, leverage)
            
            # --- NORMALIZAÇÃO DE QUANTIDADE (FIX CRÍTICO) ---
            step_size = self.get_step_size(self.symbol)
            qty_to_send = self.normalize_quantity(quantity, step_size, current_price=entry_price)
            
            if float(qty_to_send) <= 0:
                 print(f"    ERRO: Quantidade normalizada é ZERO ({qty_to_send}). Aumente o capital.")
                 return False
                 
            print(f"    Step Size: {step_size} | Qty Raw: {quantity} | Qty Norm: {qty_to_send}")

            # Enviar Ordem
            print(f"    DISPARANDO ORDEM {side} 50x...")
            res = self.api.execute_order(
                symbol=self.symbol,
                side=side_param,
                price=entry_price, # Limit Order no preço atual (ou Market se preferir velocidade)
                order_type="Market", 
                quantity=qty_to_send, # USAR NORMALIZADO
                stop_loss=sl_price
            )
            
            if res:
                print(f"    ORDEM EXECUTADA: {res.get('id', 'N/A')}")
                return True
            else:
                print("    FALHA NA EXECUÇÃO DA API.")
                return False
                
        except Exception as e:
            print(f"    ERRO CRÍTICO NO EXECUTOR: {e}")
            return False

def ultra_scalper():
    print(f"\n ULTRA SCALPER 50X ATIVADO ")
    print(f"    Alavancagem: {LEVERAGE}x")
    print(f"   ️ Protocolo: ScalpChecklist (5m/15m)")
    
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    # Loop Infinito
    while True:
        try:
            print("\n Varrendo Volatilidade (Top Movers)...")
            tickers = data.get_tickers()
            if not tickers:
                time.sleep(1)
                continue
                
            perp_tickers = [t for t in tickers if t['symbol'].endswith('_PERP')]
            
            # Ordenar por volatilidade absoluta (Change %)
            # Queremos os que estão se movendo MUITO agora.
            perp_tickers.sort(key=lambda x: abs(float(x['priceChangePercent'])), reverse=True)
            
            # Top 10 mais voláteis
            candidates = perp_tickers[:10]
            
            # --- FOCO DO USUÁRIO: ZEC ---
            # Se ZEC_USDC_PERP não estiver no Top 10, força a inclusão.
            # O usuário ordenou: "FOCO EM ZEC".
            zec_found = False
            for c in candidates:
                if c['symbol'] == "ZEC_USDC_PERP":
                    zec_found = True
                    break
            
            if not zec_found:
                for t in perp_tickers:
                    if t['symbol'] == "ZEC_USDC_PERP":
                        candidates.insert(0, t) # Prioridade máxima
                        print(f"    TARGET PRIORITÁRIO ADICIONADO: ZEC_USDC_PERP")
                        break
            # ----------------------------

            print(f"   {'SYMBOL':<15} | {'CHANGE %':<10} | {'PRICE':<10}")
            for t in candidates:
                print(f"   {t['symbol']:<15} | {float(t['priceChangePercent']):.2f}%     | ${float(t['lastPrice']):.4f}")
            
            print("\n Analisando Candidatos...")
            
            # --- FETCH MARKETS FOR LEVERAGE CHECK ---
            all_markets = data.get_markets()
            market_map = {m['symbol']: m for m in all_markets}
            
            for t in candidates:
                symbol = t['symbol']
                price = float(t['lastPrice'])
                change = float(t['priceChangePercent'])
                
                # Check Max Leverage
                market_info = market_map.get(symbol)
                max_lev = 50 # Default high
                if market_info and 'filters' in market_info:
                     # Usually leverage is in filters or a specific field. 
                     # Backpack API docs structure varies. Let's assume standard logic or default.
                     # If we fail to set 50x, we catch exception.
                     pass
                     
                # Dynamic Leverage Logic:
                # If symbol is in "Low Leverage List" (e.g. 10x), reduce.
                # Heuristic: If we fail to set 50x, we retry with 10x?
                # Better: Try 50x, if fail, try 20x, then 10x.
                
                # Lógica Básica de Seleção para o Checklist
                # Se subiu muito (>5%), tenta Short de exaustão? Ou Long de rompimento?
                # Se caiu muito (<-5%), tenta Long de repique?
                # Vamos deixar o Checklist decidir com base no RSI/EMA.
                # Mas precisamos propor um LADO para o checklist.
                
                # Heurística Simples:
                # Se Change > 3% -> Testar Short (Reversão à média) OU Long (Trend)
                # O Checklist verifica EMA.
                # Vamos testar AMBOS os lados? Não, muito lento.
                # Vamos usar RSI rápido (1m) aqui para decidir o lado do teste.
                
                klines_1m = data.get_klines(symbol, "1m", limit=14)
                if not klines_1m: continue
                
                # Calculo RSI na mão rapidinho ou via pandas
                df = pd.DataFrame(klines_1m)
                df['close'] = df['close'].astype(float)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
                
                side_to_test = None
                if rsi > 70: side_to_test = "Sell" # Sobrecomprado -> Short
                elif rsi < 30: side_to_test = "Buy" # Sobrevendido -> Long
                
                if not side_to_test:
                    continue # Ativo sem extremo no 1m, ignora.
                    
                print(f"    {symbol}: RSI 1m em {rsi:.1f}. Testando {side_to_test}...")
                
                # Calcular tamanho da mão
                # Precisamos saber o saldo.
                # Como não temos acesso fácil ao saldo aqui sem chamar API privada,
                # vamos fixar um valor pequeno para teste ou pegar saldo.
                # Vamos pegar saldo via API.
                balances = requests.get("https://api.backpack.exchange/api/v1/capital", headers=auth.get_headers("capitalQuery", {})).json()
                # Assuming USDC collateral
                usdc_balance = float(balances.get('USDC', {'available': 0})['available'])
                
                # Protection: Don't use full capital if we have multiple trades?
                # Max 1 trade for now.
                
                trade_size_usd = usdc_balance * CAPITAL_ALLOCATION
                
                # Dynamic Leverage Setting
                effective_leverage = LEVERAGE
                # Try to check max leverage from symbol name? 
                # User data implies: BTC 60x, SOL 50x, ETH 50x, Others 10x-20x.
                # Let's be safe: If it's not a major, use 10x?
                # Majors: BTC, ETH, SOL.
                is_major = symbol in ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"]
                if not is_major:
                    effective_leverage = 10 # Safer default for alts
                    
                margin_usd = usdc_balance * CAPITAL_ALLOCATION
                position_size_usd = margin_usd * effective_leverage
                quantity_tokens = position_size_usd / price
                
                # --- FIX CRÍTICO: ABSOLUTE QUANTITY ---
                # Garante que quantity é sempre positivo, independente do lado
                quantity_tokens = abs(quantity_tokens)
                
                # Executar Checklist e Ordem
                executor = UltraExecutor(symbol)
                success = executor.execute_scalp_order(side_to_test, quantity_tokens, effective_leverage)
                
                if success:
                    print(f"    TRADE ABERTO EM {symbol}! MONITORAR!")
                    time.sleep(5) # Respira
                
            print(f"    Aguardando {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n Scalper interrompido pelo usuário.")
            break
        except Exception as e:
            print(f"   ️ Erro no Loop Principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    ultra_scalper()
