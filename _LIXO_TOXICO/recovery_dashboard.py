#!/usr/bin/env python3
"""
 RECOVERY DASHBOARD - PROJECT 500
Monitora a distância para os alvos Sniper e o progresso da recuperação.
"""

import time
import os
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from dotenv import load_dotenv
from market_intelligence import MarketIntelligence

load_dotenv()

# Alvos definidos no Deep Sniper
TARGETS = {
    'SOL_USDC_PERP': 140.85,
    'ETH_USDC_PERP': 3255.00,
    'WIF_USDC_PERP': 0.3620,
    'JUP_USDC_PERP': 0.2150,
    'kBONK_USDC_PERP': 0.0104 # Novo alvo dinâmico
}

# Meta
GOAL = 500.0
CURRENT_CAPITAL = 463.0 # Estimado (Main + LFG)

def dashboard():
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    mi = MarketIntelligence()
    
    print("\n" + "="*60)
    print(f" PROJETO 500: Status de Recuperação")
    print(f"   Capital Atual: ${CURRENT_CAPITAL:.2f} | Meta: ${GOAL:.2f}")
    print(f"   Falta: ${GOAL - CURRENT_CAPITAL:.2f} ({((CURRENT_CAPITAL/GOAL)-1)*100:.1f}%)")
    
    # BTC Leader Check
    try:
        btc_ticker = data.get_ticker("BTC_USDC_PERP")
        btc_price = float(btc_ticker['lastPrice'])
        btc_klines = data.get_klines("BTC_USDC_PERP", "15m", limit=20)
        btc_rsi = mi.calculate_rsi([float(k['close']) for k in btc_klines])
        print(f"    BTC LEADER: ${btc_price:.2f} | RSI: {btc_rsi:.1f}")
    except:
        print("    BTC LEADER: N/A")
        
    print("="*60)
    print(f"{'ATIVO':<10} | {'ATUAL':<10} | {'ALVO':<10} | {'DISTÂNCIA':<10} | {'STATUS':<15}")
    print("-" * 60)
    
    # Obter Posições e Ordens para verificar proteção
    positions = data.get_positions()
    orders = data.get_open_orders()
    
    for symbol, target_price in TARGETS.items():
        try:
            # Dados
            ticker = data.get_ticker(symbol)
            price = float(ticker['lastPrice'])
            
            # RSI Rápido
            klines = data.get_klines(symbol, "15m", limit=20)
            closes = [float(k['close']) for k in klines]
            rsi = mi.calculate_rsi(closes)
            
            # Distância
            dist_pct = ((price - target_price) / price) * 100
            
            # Verificar Posição e Proteção
            pos = next((p for p in positions if p['symbol'] == symbol and float(p['netQuantity']) != 0), None)
            
            status_icon = "⏳ ESPERANDO"
            
            if pos:
                # Se tem posição, verificar SL e TP
                has_sl = False
                has_tp = False
                sym_orders = [o for o in orders if o['symbol'] == symbol]
                
                for o in sym_orders:
                    # SL Check (Stop Market/Limit)
                    if (o.get('orderType') == 'StopMarket' or o.get('triggerPrice')) and \
                       o.get('side') != ('Long' if float(pos['netQuantity']) > 0 else 'Short'): 
                         has_sl = True
                    # TP Check (Limit Reduce Only)
                    if o.get('orderType') == 'Limit' and o.get('reduceOnly') and \
                       o.get('side') != ('Long' if float(pos['netQuantity']) > 0 else 'Short'):
                         has_tp = True
                         
                if has_sl and has_tp:
                    status_icon = "️ PROTEGIDO"
                elif has_sl:
                    status_icon = "️ SÓ SL"
                elif has_tp:
                    status_icon = "️ SÓ TP"
                else:
                    status_icon = " EXPOSTO"
            
            elif dist_pct < 0.5: 
                status_icon = " PERTO"
            
            rsi_color = "🟢" if rsi < 30 else ""
            
            print(f"{symbol.split('_')[0]:<10} | ${price:<9.2f} | ${target_price:<9.2f} | {dist_pct:>5.2f}% | {status_icon} (RSI {rsi:.0f})")
            
        except Exception as e:
            print(f"Erro {symbol}: {e}")
            
    print("-" * 60)
    print(" ESTRATÉGIA: Active Sniper + Risk Manager (SL 2% / TP 4%)")
    print("   Proteção Blindada ativada.")
    print("="*60)

if __name__ == "__main__":
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        dashboard()
        time.sleep(30)