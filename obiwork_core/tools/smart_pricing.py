import os
import sys
import asyncio
from dotenv import load_dotenv

# Adicionar caminhos
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'core'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

async def analyze_costs():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    
    symbol = "BTC_USDC_PERP"
    
    print(f"--- ANÁLISE DE CUSTOS E SPREAD: {symbol} ---")
    
    # 1. Obter Order Book (Spread)
    depth = await asyncio.to_thread(data.get_orderbook_depth, symbol)
    if not depth:
        print("Erro ao obter Depth.")
        return

    best_bid = float(depth['bids'][0][0])
    best_ask = float(depth['asks'][0][0])
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    spread_pct = (spread / mid_price) * 100
    
    print(f"Preço Atual: ${mid_price:,.2f}")
    print(f"Spread: ${spread:.2f} ({spread_pct:.5f}%)")
    
    # 2. Taxas (Backpack Futures - Estimativa Tabela Padrão)
    # Maker: 0.02% | Taker: 0.05%
    maker_fee_pct = 0.02
    taker_fee_pct = 0.05
    
    # Cenário 1: Sniper Puro (Maker Entry + Maker Exit)
    # Idealmente sai no PostOnly Limit, mas as vezes pega Taker no Stop.
    cost_maker_maker = maker_fee_pct + maker_fee_pct # 0.04%
    
    # Cenário 2: Normal (Maker Entry + Taker Exit/TP Market)
    cost_maker_taker = maker_fee_pct + taker_fee_pct # 0.07%
    
    # Adicionar Spread ao custo (pois você paga o spread para entrar/sair se for taker ou se esperar o preço cruzar)
    # Se formos Maker, "ganhamos" o spread se formos preenchidos, mas precisamos que o mercado ande.
    # Para garantir lucro, o preço tem que andar: Taxas + Spread (se quisermos sair a mercado) ou Taxas (se sairmos limit).
    
    print(f"\n--- CUSTOS OPERACIONAIS ---")
    print(f"Taxa Maker (Entrada): {maker_fee_pct}%")
    print(f"Taxa Maker (Saída):   {maker_fee_pct}%")
    print(f"Custo Total (Roundtrip Maker): {cost_maker_maker}%")
    
    # 3. Cálculo do Alvo
    # Break-Even: Preço tem que mover 0.04% a favor.
    break_even_move = mid_price * (cost_maker_maker / 100)
    
    # Margem de Lucro Mínima (Ex: 0.05% Net)
    desired_net_profit = 0.05 
    required_gross_move_pct = cost_maker_maker + desired_net_profit
    required_price_move = mid_price * (required_gross_move_pct / 100)
    
    print(f"\n--- ALVOS DINÂMICOS (Limit Orders) ---")
    print(f"Break-Even (0% Lucro): Mover ${break_even_move:.2f} ({cost_maker_maker:.3f}%)")
    print(f"Alvo Mínimo (Lucro {desired_net_profit}%): Mover ${required_price_move:.2f} ({required_gross_move_pct:.3f}%)")
    
    tp_long = best_bid + required_price_move
    tp_short = best_ask - required_price_move
    
    print(f"\n>> RECOMENDAÇÃO DE PREÇO (LIMIT):")
    print(f"LONG Entry: ${best_bid:.2f} -> TP: ${tp_long:.2f}")
    print(f"SHORT Entry: ${best_ask:.2f} -> TP: ${tp_short:.2f}")
    
    print(f"\nResumo: Para pagar taxas e lucrar, precisamos de um movimento de ~{required_gross_move_pct:.3f}%.")

if __name__ == "__main__":
    asyncio.run(analyze_costs())
