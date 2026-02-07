import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.technical_oracle import TechnicalOracle

async def diagnose():
    load_dotenv()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data = BackpackData(auth)
    oracle = TechnicalOracle(data)
    
    # Posições identificadas na imagem
    # APT (Short - Lucro), BTC (Long - Preju), SOL (Long - Preju)
    targets = [
        {"symbol": "APT_USDC_PERP", "side": "Short", "pnl": "Profit"},
        {"symbol": "BTC_USDC_PERP", "side": "Long", "pnl": "Loss"},
        {"symbol": "SOL_USDC_PERP", "side": "Long", "pnl": "Loss"}
    ]
    
    print("\n DIAGNÓSTICO DE PROBABILIDADE DE REVERSÃO\n")
    print(f"{'ATIVO':<10} | {'POSIÇÃO':<6} | {'OBI (FLUXO)':<10} | {'VEREDITO':<20}")
    print("-" * 60)
    
    for t in targets:
        try:
            depth = data.get_orderbook_depth(t['symbol'])
            obi = oracle.calculate_obi(depth)
            
            # Interpretação
            verdict = "NEUTRO"
            score = 0
            
            if t['side'] == "Long":
                # Queremos OBI Positivo para subir
                if obi > 0.2: verdict = "🟢 RECUPERAÇÃO PROVÁVEL"; score = 1
                elif obi < -0.2: verdict = " QUEDA CONTINUA (RISCO)"; score = -1
                else: verdict = "🟡 INCERTO (AGUARDAR)"
            else: # Short
                # Queremos OBI Negativo para continuar caindo (Lucro)
                if obi < -0.2: verdict = "🟢 LUCRO TENDE A AUMENTAR"; score = 1
                elif obi > 0.2: verdict = " REPIQUE IMINENTE (SAIR)"; score = -1
                else: verdict = "🟡 INCERTO (MANTER STOP)"
                
            print(f"{t['symbol']:<10} | {t['side']:<6} | {obi:>6.2f}     | {verdict}")
            
        except Exception as e:
            print(f"{t['symbol']:<10} | ERRO: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(diagnose())
