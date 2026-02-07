import sys
import os
import logging

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vsc_brain import VSCBrain

def diagnose_btc():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("BTC_Diagnosis")
    brain = VSCBrain()
    
    # DADOS REAIS/ESTIMADOS DE HOJE (04/02/2026 - CRASH)
    btc_market_data = {
        'price': 73200.0,
        'funding': 0.0001,      # Funding ainda positivo (Crowded Longs sofrendo)
        'netflow': 5000000,     # Netflow Positivo (Inflow para Exchange = Pressão de Venda de ETFs)
        'oi_delta': -0.05,      # OI Caindo (-5% = Liquidações)
        'rsi': 28.5,            # RSI Sobrevendido (Oversold Extremo)
        'obi': -0.2             # Orderbook com leve pressão vendedora, mas não colapso total
    }

    logger.info(" DIAGNÓSTICO VSC: BITCOIN (BTC_USDC) ")
    logger.info(f"Dados: {btc_market_data}\n")

    # Teste 1: Intenção de LONG (Pegar a faca caindo?)
    approved_long, reason_long, size_long = brain.validate_entry("BTC_USDC", "LONG", btc_market_data)
    logger.info(f" Intenção LONG: {approved_long} | Size: {size_long} | Motivo: {reason_long}")

    # Teste 2: Intenção de SHORT (Seguir a tendência?)
    approved_short, reason_short, size_short = brain.validate_entry("BTC_USDC", "SHORT", btc_market_data)
    logger.info(f" Intenção SHORT: {approved_short} | Size: {size_short} | Motivo: {reason_short}")

if __name__ == "__main__":
    diagnose_btc()
