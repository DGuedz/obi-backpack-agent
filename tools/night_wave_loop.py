import asyncio
import os
import sys
import time
import subprocess
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from backpack_transport import BackpackTransport
from backpack_data import BackpackData
from backpack_auth import BackpackAuth
from technical_oracle import TechnicalOracle

# Setup simples de log
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - NIGHT WATCH - %(message)s')
logger = logging.getLogger("NightWaveLoop")

async def run_night_loop():
    load_dotenv()
    
    # Init Components
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    oracle = TechnicalOracle(data_client)
    
    current_process = None
    
    print("\n NIGHT WAVE LOOP INITIATED")
    print("   -> Strategy: Wave Surfing (Trend + Flow)")
    print("   -> Cycle: Every 30 minutes")
    print("-" * 60)
    
    while True:
        try:
            logger.info(" Scanning for Night Waves...")
            
            # 1. Get all PERPs
            tickers = data_client.get_tickers()
            perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
            
            # Filter low volume to avoid stuck capital
            perps = [p for p in perps if float(p.get('quoteVolume', 0)) > 100000] # >100k vol
            
            candidates = []
            
            for p in perps:
                symbol = p['symbol']
                # Quick Compass Check
                try:
                    compass = oracle.get_market_compass(symbol)
                    score = compass.get('score', 0)
                    obi = compass.get('obi', 0)
                    
                    # WAVE CRITERIA (MADRUGADA)
                    # Madrugada tem menos volume, então precisamos de Tendência Clara ou Fluxo Forte.
                    # Score > 70 indica confluência de Trend + OBI + Volatility controlada.
                    
                    if score >= 65: # Threshold levemente reduzido para pegar início de movimentos
                        candidates.append({
                            'symbol': symbol,
                            'score': score,
                            'obi': obi,
                            'trend': compass.get('direction'),
                            'spread': float(p.get('lastPrice',0)) # Just placeholder, real spread check inside compass
                        })
                except:
                    continue
            
            # Sort by Score desc
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Pick Top 5
            top_waves = candidates[:5]
            
            if not top_waves:
                logger.warning("️ No clear waves detected. Sleeping 5 min...")
                await asyncio.sleep(300)
                continue
                
            symbols_to_farm = [c['symbol'] for c in top_waves]
            logger.info(f" Top Waves Detected: {symbols_to_farm}")
            for w in top_waves:
                logger.info(f"   -> {w['symbol']}: Score {w['score']} | OBI {w['obi']:.2f} | {w['trend']}")
            
            # 2. Restart Volume Farmer with new targets
            if current_process:
                logger.info(" Stopping previous farmer instance...")
                current_process.terminate()
                try:
                    current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_process.kill()
            
            cmd = [
                "python3", "tools/volume_farmer.py",
                "--turbo",
                "--leverage", "10",
                "--size", "6.0", # Micro Size Safety
                "--symbols"
            ] + symbols_to_farm
            
            logger.info(f" Launching Volume Farmer on {len(symbols_to_farm)} assets...")
            current_process = subprocess.Popen(cmd)
            
            # 3. Wait for next cycle
            # Madrugada cycles can be longer to let trades play out
            # 30 minutes seems appropriate for "Wave" surfing
            await asyncio.sleep(1800) 
            
        except Exception as e:
            logger.error(f"Critical Loop Error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_night_loop())
