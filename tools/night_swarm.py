import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from core.risk_manager import RiskManager
from core.precision_guardian import PrecisionGuardian

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NightSwarm")

async def night_swarm_attack():
    """
     NIGHT SWARM PROTOCOL (MASSIVE ATTACK - DAEMON MODE)
    Divide a margem disponível em 10 fatias e ataca os 10 ativos mais líquidos simultaneamente.
    Objetivo: Diversificação extrema para farmar volume e reduzir risco de ruína por ativo único.
    """
    logger.info(" INICIANDO NIGHT SWARM COMMANDER (DAEMON MODE)...")
    logger.info("ℹ️  Estratégia: Pulverização (10 Ativos) | Alavancagem: 5x (Segurança) | TP: 1.5%")
    
    load_dotenv()
    
    transport = BackpackTransport()
    auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
    data_client = BackpackData(auth)
    risk_manager = RiskManager(transport)
    guardian = PrecisionGuardian(transport)
    
    while True:
        try:
            logger.info(" INICIANDO CICLO DE ATAQUE DO SWARM...")
            
            # 1. Obter Capital Disponível
            safe, usable_capital = risk_manager.check_capital_safety()
            if not safe:
                logger.warning(" Capital insuficiente ou Regra de Reserva violada. Aguardando margem liberar...")
                await asyncio.sleep(60) # Espera 1 minuto antes de tentar de novo
                continue

            logger.info(f" Capital Operacional (Swarm): ${usable_capital:.2f}")
            
            # 2. Definir Tamanho da Fatia (10% do Capital por Ativo)
            SWARM_SIZE = 10
            slice_capital = usable_capital / SWARM_SIZE
            
            # Validação Mínima
            if slice_capital < 1.0:
                logger.warning(f"️ Capital por fatia (${slice_capital:.2f}) muito baixo. Reduzindo número de alvos.")
                SWARM_SIZE = int(usable_capital / 2.0)
                if SWARM_SIZE < 1:
                    logger.warning(" Capital insuficiente para sequer 1 posição mínima. Dormindo...")
                    await asyncio.sleep(60)
                    continue
                slice_capital = usable_capital / SWARM_SIZE
                logger.info(f" Novo Swarm Size: {SWARM_SIZE} ativos | ${slice_capital:.2f} margem cada.")

            # 3. Selecionar Top Ativos (Volume)
            logger.info(" Selecionando Top Targets por Volume e Qualidade...")
            try:
                tickers = data_client.get_tickers()
                perps = [t for t in tickers if 'PERP' in t.get('symbol', '')]
                perps.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
                
                # Filtro de Blacklist (Evitar ativos quebrados/iliquidos se houver)
                blacklist = ["ZORA_USDC_PERP"] # Exemplo
                
                # Quality Filter
                candidates = [t['symbol'] for t in perps if t['symbol'] not in blacklist]
                
                # Selecionar até SWARM_SIZE * 2 para ter reserva caso falhe no check de qualidade
                target_candidates = candidates[:SWARM_SIZE * 2]
                
                final_targets = []
                
                # Trend Quality Check
                logger.info(f" Analisando qualidade técnica de {len(target_candidates)} candidatos...")
                for cand in target_candidates:
                    if len(final_targets) >= SWARM_SIZE:
                        break
                        
                    klines = data_client.get_klines(cand, "15m", limit=55)
                    if not klines: continue
                    
                    closes = [float(k['close']) for k in klines]
                    current = closes[-1]
                    
                    # Simple EMA50
                    k = 2 / (50 + 1)
                    ema = closes[0]
                    for c in closes[1:]:
                        ema = (c * k) + (ema * (1 - k))
                        
                    # Trend Clarity Ratio
                    dist_pct = abs(current - ema) / ema
                    if dist_pct < 0.002: # 0.2% Noise Filter
                        logger.warning(f"️ {cand} REJEITADO: Mercado Lateral (Dist: {dist_pct*100:.2f}%)")
                        continue
                        
                    final_targets.append(cand)
                    
                targets = final_targets
                logger.info(f" ALVOS FINAIS ({len(targets)}): {targets}")
                
            except Exception as e:
                logger.error(f" Falha ao buscar tickers: {e}")
                await asyncio.sleep(30)
                continue

            # 4. Execução Massiva (Batch)
            logger.info(" EXECUTANDO ATAQUE MASSIVO (SWARM LAUNCH)...")
            
            LEVERAGE = 5 # 5x para dormir tranquilo
            
            for symbol in targets:
                try:
                    # Check if already open
                    positions = transport.get_positions()
                    is_open = False
                    if positions:
                        for p in positions:
                            if p['symbol'] == symbol:
                                is_open = True
                                break
                    
                    if is_open:
                        logger.info(f"⏭️ {symbol} já possui posição. Pulando.")
                        continue
                        
                    # Analisar Tendência Rápida
                    klines = data_client.get_klines(symbol, "15m", limit=55)
                    if not klines:
                        continue
                        
                    closes = [float(k['close']) for k in klines]
                    current_price = closes[-1]
                    ema50 = sum(closes[-50:]) / 50 
                    
                    # EMA real calculation again
                    k = 2 / (50 + 1)
                    ema = closes[0]
                    for c in closes[1:]:
                        ema = (c * k) + (ema * (1 - k))
                    
                    trend = "LONG" if current_price > ema else "SHORT"
                    side = "Buy" if trend == "LONG" else "Sell"
                    
                    # Calcular Quantidade
                    notional = slice_capital * LEVERAGE
                    qty_raw = notional / current_price
                    qty_fmt = guardian.format_quantity(symbol, qty_raw)
                    
                    # Executar Market
                    logger.info(f" {side} {symbol} | Size: {qty_fmt} (~${notional:.2f}) | Trend: {trend}")
                    
                    res = transport.execute_order(symbol, "Market", side, qty_fmt)
                    
                    if res:
                        logger.info(f"    Ordem enviada com sucesso!")
                        await asyncio.sleep(1)
                        
                        # Calculate Prices
                        entry = current_price
                        if side == "Buy":
                            tp_price = entry * 1.015
                            sl_price = entry * 0.85 
                            tp_side = "Sell"
                        else:
                            tp_price = entry * 0.985
                            sl_price = entry * 1.15
                            tp_side = "Buy"
                        
                        tp_fmt = guardian.format_price(symbol, tp_price)
                        sl_fmt = guardian.format_price(symbol, sl_price)
                        
                        # TP (Limit)
                        transport.execute_order(symbol, "Limit", tp_side, qty_fmt, price=tp_fmt)
                        # SL (StopMarket)
                        payload_sl = {
                            "symbol": symbol, 
                            "side": tp_side, 
                            "orderType": "StopMarket", 
                            "quantity": qty_fmt, 
                            "triggerPrice": sl_fmt,
                            "triggerQuantity": qty_fmt
                        }
                        transport._send_request("POST", "/api/v1/order", "orderExecute", payload_sl)
                        
                        logger.info(f"   ️ TP ({tp_fmt}) e SL ({sl_fmt}) configurados.")
                        
                    else:
                        logger.error(f"    Falha na execução para {symbol}")
                        
                except Exception as e:
                    logger.error(f"️ Erro ao processar {symbol}: {e}")
                    continue
                    
            logger.info(" CICLO SWARM COMPLETO. Dormindo 5 minutos...")
            await asyncio.sleep(300) # Sleep 5 minutes
            
        except Exception as e:
            logger.error(f" ERRO FATAL NO LOOP: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(night_swarm_attack())
