import asyncio
import pandas as pd
import numpy as np
import sys
import os
from dotenv import load_dotenv

# Configuração de Caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth

# --- CONFIGURAÇÃO DA SIMULAÇÃO (WEAVER MODULAR 1D) ---
SYMBOL = "BTC_USDC_PERP"
TIMEFRAME = "1d"
LIMIT = 100
CAPITAL_INICIAL = 1000.0
LEVERAGE = 5 
MAKER_FEE = 0.0003
TAKER_FEE = 0.0008

# Weaver Config (Adaptado para Diário)
GRID_STEP = 0.02 # 2% de queda entre balas (Diário exige range maior)
TARGET_PROFIT = 0.03 # 3% de Alvo sobre o Preço Médio
STOP_LOSS_PCT = 0.10 # 10% do Preço Médio (Stop de Catástrofe)

async def run_simulation():
    print(f"\n️ SIMULAÇÃO WEAVER GRID (MODULAR) - BTC DAILY")
    print(f"   Capital: ${CAPITAL_INICIAL} | Lev: {LEVERAGE}x")
    print(f"   Grid: Scout (20%) -> -{GRID_STEP*100}% Soldier (30%) -> -{GRID_STEP*2*100}% Tank (50%)")
    print(f"   Alvo: Preço Médio + {TARGET_PROFIT*100}%")
    print("-" * 100)

    # 1. Carregar Dados
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    
    klines = data_client.get_klines(SYMBOL, TIMEFRAME, limit=LIMIT)
    if not klines: return

    df = pd.DataFrame(klines)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    # Bollinger Bands (20, 2)
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['std_dev'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['sma_20'] + (2 * df['std_dev'])
    df['bb_lower'] = df['sma_20'] - (2 * df['std_dev'])
    
    capital = CAPITAL_INICIAL
    volume_gerado = 0.0
    wins = 0
    losses = 0
    
    # Estado da Posição
    pos = {
        "active": False,
        "side": None,
        "avg_price": 0.0,
        "total_qty": 0.0,
        "bullets_fired": 0, # 0, 1, 2, 3
        "scout_price": 0.0 # Referência
    }

    print(f"{'DATA':<5} | {'EVENTO':<10} | {'PREÇO':<10} | {'AVG PRICE':<10} | {'BALAS':<5} | {'LUCRO':<10} | {'CAPITAL':<10}")
    print("-" * 100)

    for i in range(20, len(df)):
        row = df.iloc[i]
        close = row['close']
        low = row['low']
        high = row['high']
        bb_lower = row['bb_lower']
        
        # --- LÓGICA WEAVER (LONG ONLY PARA SIMPLIFICAÇÃO) ---
        
        # 1. ENTRADA (Scout)
        if not pos["active"]:
            if low <= bb_lower:
                # Dispara Scout (20%)
                pos["active"] = True
                pos["side"] = "Long"
                pos["scout_price"] = bb_lower # Assume entrada na banda
                pos["bullets_fired"] = 1
                
                # Tamanho
                margin = capital * 0.20
                notional = margin * LEVERAGE
                qty = notional / pos["scout_price"]
                
                pos["total_qty"] = qty
                pos["avg_price"] = pos["scout_price"]
                volume_gerado += notional
                
                print(f"Dia {i:<3} | 🟢 SCOUT   | {pos['scout_price']:<10.2f} | {pos['avg_price']:<10.2f} | 1/3   | {'-':<10} | {capital:<10.2f}")

        # 2. GESTÃO (Soldier & Tank & Saída)
        elif pos["active"] and pos["side"] == "Long":
            # Verificar Trigger de Novas Balas (DCA) com base no LOW do dia
            
            # Soldier (Scout - 2%)
            if pos["bullets_fired"] == 1 and low <= pos["scout_price"] * (1 - GRID_STEP):
                bullet_price = pos["scout_price"] * (1 - GRID_STEP)
                margin = capital * 0.30
                notional = margin * LEVERAGE
                qty = notional / bullet_price
                
                # Recalcular Médio
                total_val = (pos["total_qty"] * pos["avg_price"]) + notional
                pos["total_qty"] += qty
                pos["avg_price"] = total_val / pos["total_qty"]
                pos["bullets_fired"] = 2
                volume_gerado += notional
                
                print(f"Dia {i:<3} | ️ SOLDIER | {bullet_price:<10.2f} | {pos['avg_price']:<10.2f} | 2/3   | {'-':<10} | {capital:<10.2f}")

            # Tank (Scout - 5% aprox, ou Soldier - 3%)
            if pos["bullets_fired"] == 2 and low <= pos["scout_price"] * (1 - (GRID_STEP * 2.5)):
                bullet_price = pos["scout_price"] * (1 - (GRID_STEP * 2.5))
                margin = capital * 0.50
                notional = margin * LEVERAGE
                qty = notional / bullet_price
                
                total_val = (pos["total_qty"] * pos["avg_price"]) + notional
                pos["total_qty"] += qty
                pos["avg_price"] = total_val / pos["total_qty"]
                pos["bullets_fired"] = 3
                volume_gerado += notional
                
                print(f"Dia {i:<3} |  TANK    | {bullet_price:<10.2f} | {pos['avg_price']:<10.2f} | 3/3   | {'-':<10} | {capital:<10.2f}")

            # 3. SAÍDA (Target Profit ou Stop Loss)
            
            # Target (Baseado no HIGH do dia)
            target_price = pos["avg_price"] * (1 + TARGET_PROFIT)
            stop_price = pos["avg_price"] * (1 - STOP_LOSS_PCT)
            
            exit_price = 0.0
            exit_reason = ""
            
            if high >= target_price:
                exit_price = target_price
                exit_reason = " TARGET"
            elif low <= stop_price:
                exit_price = stop_price
                exit_reason = " STOP"
                
            if exit_price > 0:
                # Executar Saída
                raw_pnl = (exit_price - pos["avg_price"]) * pos["total_qty"]
                
                # Taxas (Entrada Maker foi considerada free/rebate no calculo simples, mas vamos cobrar
                # Saída Taker
                # Simplificando: Cobrar Maker Fee sobre todo volume de entrada e Taker na saida
                # Entrada foi fracionada, mas vamos somar o volume total
                
                total_entry_vol = pos["total_qty"] * pos["avg_price"]
                entry_fees = total_entry_vol * MAKER_FEE
                exit_fees = (exit_price * pos["total_qty"]) * TAKER_FEE
                
                net_pnl = raw_pnl - (entry_fees + exit_fees)
                
                capital += net_pnl
                volume_gerado += (exit_price * pos["total_qty"])
                
                if net_pnl > 0: wins += 1
                else: losses += 1
                
                print(f"Dia {i:<3} | {exit_reason:<10} | {exit_price:<10.2f} | {'-':<10} | 0/3   | ${net_pnl:<9.2f} | {capital:<10.2f}")
                
                # Reset
                pos["active"] = False
                pos["bullets_fired"] = 0
                pos["total_qty"] = 0

    print("-" * 100)
    print(f" RESULTADO WEAVER RECALCULADO:")
    print(f"   Capital Final: ${capital:.2f} ({(capital - CAPITAL_INICIAL)/CAPITAL_INICIAL*100:.1f}%)")
    print(f"   Volume Total: ${volume_gerado:,.2f}")
    print(f"   Trades: {wins+losses} (Wins: {wins} | Losses: {losses})")
    if wins+losses > 0:
        print(f"   Win Rate: {(wins/(wins+losses))*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(run_simulation())
