import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from core.risk_manager import RiskManager
from strategies.sniper_executor import SniperExecutor

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print(" INICIANDO MODO VOLUME FARM (RECOVERY & AIRDROP)...")
    print("️  ATENÇÃO: TP Automático 2% | Alavancagem 10x")
    print("️  Foco: Recuperar Saldo ($250) e Gerar Volume ($1M)")
    
    # Load Environment
    load_dotenv()
    
    # Init Dependencies
    # Note: BackpackTransport loads keys from env internally if not provided, 
    # but we pass auth to DataClient.
    transport = BackpackTransport() 
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    risk_manager = RiskManager(transport)
    
    # Init Sniper
    sniper = SniperExecutor(transport, data_client, risk_manager)
    
    # Set Aggressive Mode
    sniper.set_mode("S4_FINALE") # MODO S4 FINALE (High Freq + 1M Vol Target)
    
    # 1. Definir Alvos (Prioridade: Argumentos CLI > Lista Estática)
    if len(sys.argv) > 1:
        # Se argumentos passados (ex: python aggressive_hunter.py BTC_USDC_PERP SOL_USDC_PERP)
        targets = sys.argv[1:]
        print(f" WAVES CARREGADAS VIA CLI: {targets}")
    else:
        # Fallback para Lógica Antiga
        print(" Atualizando lista de Top Ativos Líquidos & Hot Rates...")
        try:
            tickers = data_client.get_tickers()
            perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
            # Ordenar por Volume (quoteVolume)
            perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
            # Top 10 + HYPE (Manual Override)
            top_targets = [t['symbol'] for t in perps[:10]]
            
            # HOT ALPHA ASSETS (Baseado no Relatório do Mestre)
            # Funding Negativo (Bom para Long): FRAG, JTO, MNT, ZORA, FLOCK, AVNT
            # Funding Positivo (Bom para Short): MON (11%!), SOL, USD, BNB
            alpha_assets = [
                "MON_USDC_PERP", "FRAG_USDC_PERP", "JTO_USDC_PERP", "MNT_USDC_PERP", 
                "ZORA_USDC_PERP", "FLOCK_USDC_PERP", "AVNT_USDC_PERP", "SOL_USDC_PERP",
                "BNB_USDC_PERP", "DOGE_USDC_PERP", "HYPE_USDC_PERP", "BTC_USDC_PERP",
                "ETH_USDC_PERP", "SUI_USDC_PERP", "APT_USDC_PERP"
            ]
            
            # Merge Unique
            final_targets = list(set(top_targets + alpha_assets))
            
            # Prioritize Alpha (Move to front)
            final_targets.sort(key=lambda x: x in alpha_assets, reverse=True)
            
            targets = final_targets
        except Exception as e:
            print(f"️ Falha ao buscar top tickers: {e}. Usando lista estática Alpha.")
            targets = ["MON_USDC_PERP", "FRAG_USDC_PERP", "JTO_USDC_PERP", "SOL_USDC_PERP", "BNB_USDC_PERP", "BTC_USDC_PERP"]
    
    print(f" ALVOS DEFINIDOS ({len(targets)}): {targets}")
    print(" MONITORANDO FLUXO (BÚSSOLA OBI > 0.25) E OI...")
    print(" MODO ALADDIN ATIVADO: Latência Mínima.")
    
    try:
        while True:
            start_time = asyncio.get_event_loop().time()
            # SWARM MODE: Create tasks for all targets to run in parallel
            tasks = [sniper.scan_and_execute(symbol) for symbol in targets]
            
            # Run all tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = asyncio.get_event_loop().time() - start_time
            print(f"⏳ Ciclo ALADDIN concluído em {elapsed:.2f}s.")
            
            # Stagnation Monitor (Async)
            await sniper.monitor_stagnation()
            
            await asyncio.sleep(0.5) # 0.5s Latency (Institutional Speed)
            
    except KeyboardInterrupt:
        print("\n Caçada Encerrada pelo Usuário.")

if __name__ == "__main__":
    asyncio.run(main())
