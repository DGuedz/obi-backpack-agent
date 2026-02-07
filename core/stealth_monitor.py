import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle
from position_manager import PositionManager
from book_scanner import BookScanner

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stealth_monitor.log"),
        logging.StreamHandler()
    ]
)

async def stealth_monitor():
    load_dotenv()
    logger = logging.getLogger("StealthMonitor")
    logger.info(" STEALTH MONITOR INICIADO (Modo Passivo)")
    logger.info("   -> Monitorando posições, ajustando TP (Maker) e SL (Safety).")
    logger.info("   -> Wall Guardian & OBI Rescue Ativos.")

    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    pos_manager = PositionManager(transport)
    scanner = BookScanner()
    
    counter = 0

    while True:
        try:
            wall_intel = {}
            obi_data = {}
            
            # Rodar Scanner a cada 60s (6 loops de 10s)
            if counter % 6 == 0:
                print("\n Scanning Order Book Walls & OBI...", end="", flush=True)
                wall_intel = scanner.scan(return_data=True)
                
                # Fetch OBI for active positions
                positions = transport.get_positions()
                if positions:
                    for pos in positions:
                        symbol = pos.get('symbol')
                        depth = data_client.get_orderbook_depth(symbol)
                        if depth:
                            obi = oracle.calculate_obi(depth)
                            obi_data[symbol] = obi
                            # print(f" [OBI {symbol}: {obi:+.2f}]", end="")
            
            # 1. Gerenciar Posições (TP Maker, SL, Trailing, Wall Guard, OBI Rescue)
            pos_manager.manage_positions(wall_intel, obi_data)
            
            # 2. Heartbeat Visual
            print(".", end="", flush=True)
            
            counter += 1
            await asyncio.sleep(10) # Scan a cada 10s
            
        except KeyboardInterrupt:
            logger.info("\n Monitoramento Interrompido pelo Usuário.")
            break
        except Exception as e:
            logger.error(f"Erro no Loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(stealth_monitor())
