import sys
import os
import time
from dotenv import load_dotenv

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.backpack_transport import BackpackTransport
from core.technical_oracle import TechnicalOracle

def calculate_smart_margin():
    print(" CALCULADORA DE MARGEM INTELIGENTE (Agulhadas & Violinadas Proof)")
    print("================================================================")
    
    load_dotenv()
    
    # 1. Inicializar Clientes
    client = BackpackTransport()
    oracle = TechnicalOracle(client)
    
    # 2. Obter Saldo e Margem
    print(" Analisando Carteira e Margem...")
    try:
        collateral = client.get_account_collateral()
        
        if not collateral:
            print(" Erro ao obter dados da conta.")
            return

        available_margin = float(collateral.get('netEquityAvailable', 0))
        equity = float(collateral.get('netEquity', 0))
        
        print(f" Equity Total:      ${equity:.2f}")
        print(f" Margem Disponível: ${available_margin:.2f}")
        
        if available_margin < 2:
            print("️ Margem Crítica! (Menor que $2). Impossível abrir novas posições.")
            return

    except Exception as e:
        print(f" Erro ao ler saldo: {e}")
        return

    # 3. Lista de Elite (Do Scanner)
    elite_assets = ['SKR_USDC_PERP', 'IP_USDC_PERP', 'XLM_USDC_PERP', 'ZRO_USDC_PERP', 'XRP_USDC_PERP', 'PAXG_USDC_PERP', 'HYPE_USDC_PERP', 'PENDLE_USDC_PERP']
    
    print(f"\n Analisando {len(elite_assets)} Ativos da Lista de Elite...")
    print("   (Buscando Oportunidades com Proteção contra Volatilidade)")
    
    viable_entries = []
    
    for symbol in elite_assets:
        try:
            compass = oracle.get_market_compass(symbol)
            score = compass['score']
            direction = compass['direction']
            vol_risk = compass['volatility_risk']
            sl_dist = compass['stop_loss_dist']
            suggested_lev = compass['suggested_leverage']
            price = compass['current_price']
            
            # User Rule: Max 10x leverage
            leverage = min(10, suggested_lev)
            if vol_risk == 'HIGH': leverage = min(5, leverage) # Reduce leverage for high vol
            
            # Check OBI (already in compass reasons or accessible?)
            # Compass doesn't explicitly return OBI in top level dict, but it's in reasons strings.
            # Let's recalculate or trust score.
            # Score > 50 implies some positive factors.
            # Let's be strict: Score >= 60 for entry.
            
            status = " NEUTRO"
            if score >= 60:
                status = "🟢 VIÁVEL"
                
                # Calculate Safe Stop Loss Price
                if direction == "BULLISH":
                    sl_price = price * (1 - sl_dist)
                    entry_type = "LONG"
                else:
                    sl_price = price * (1 + sl_dist)
                    entry_type = "SHORT"
                
                # Estimate Liquidation Price at 10x (approx)
                # Liq Dist approx 1/Leverage. 10x -> 10%.
                # If SL Dist > 10%, we can't use 10x.
                # Max Leverage allowed by SL = 1 / sl_dist * 0.8 (Safety buffer)
                max_safe_lev = int((1 / sl_dist) * 0.8)
                final_lev = min(leverage, max_safe_lev)
                final_lev = max(1, final_lev) # Min 1x
                
                # Minimum Notional Check (Backpack usually $5-$10)
                min_notional = 12.0 # Safe minimum
                margin_cost = min_notional / final_lev
                
                entry_info = {
                    'symbol': symbol,
                    'type': entry_type,
                    'score': score,
                    'leverage': final_lev,
                    'sl_dist': sl_dist * 100,
                    'sl_price': sl_price,
                    'margin_cost': margin_cost,
                    'vol_risk': vol_risk
                }
                viable_entries.append(entry_info)
                
            print(f"    {symbol:<15} | Score: {score:<3} | {direction:<7} | Vol: {vol_risk:<6} | SL: {sl_dist*100:.1f}% -> {status}")
            
        except Exception as e:
            print(f"    Erro em {symbol}: {e}")

    # 4. Plano de Alocação
    print("\n PLANO DE ATAQUE (Max Entries Calculation):")
    print("------------------------------------------------")
    
    if not viable_entries:
        print(" Nenhuma oportunidade viável encontrada com os critérios atuais.")
        return

    # Sort by Score (Highest first)
    viable_entries.sort(key=lambda x: x['score'], reverse=True)
    
    total_margin_needed = 0
    selected_entries = []
    
    print(f"{'SYMBOL':<15} | {'TYPE':<5} | {'LEV':<3} | {'SL DIST':<8} | {'MARGIN($)':<10} | {'SCORE':<5}")
    
    for entry in viable_entries:
        if total_margin_needed + entry['margin_cost'] <= available_margin * 0.95: # 95% usage cap
            selected_entries.append(entry)
            total_margin_needed += entry['margin_cost']
            print(f"{entry['symbol']:<15} | {entry['type']:<5} | {entry['leverage']:<3}x | {entry['sl_dist']:<6.1f}% | ${entry['margin_cost']:<9.2f} | {entry['score']}")
        else:
            print(f"{entry['symbol']:<15} | {entry['type']:<5} | (SEM MARGEM) - Ignorado")
            
    print("------------------------------------------------")
    print(f" Total de Entradas Possíveis: {len(selected_entries)}")
    print(f" Margem Total Necessária:     ${total_margin_needed:.2f}")
    print(f" Margem Restante (Buffer):    ${available_margin - total_margin_needed:.2f}")
    
    if len(selected_entries) > 0:
        print("\n CONCLUSÃO:")
        print(f"Podemos abrir {len(selected_entries)} novas posições agora com segurança.")
        print("O cálculo considerou a volatilidade (ATR) para definir Stop Loss que aguenta 'violinadas'.")
        print("A alavancagem foi ajustada dinamicamente para garantir que o Stop Loss venha ANTES da Liquidação.")

if __name__ == "__main__":
    calculate_smart_margin()
