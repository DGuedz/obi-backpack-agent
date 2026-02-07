import sys
import os
import logging

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vsc_brain import VSCBrain

def run_simulation():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger("Simulator")
    brain = VSCBrain()
    
    logger.info("️ INICIANDO SIMULADOR DE FAKE MOVES & VETOS ️\n")

    scenarios = [
        {
            "name": "CENÁRIO 1: Perfect Setup (Goldilocks)",
            "action": "LONG",
            "data": {'funding': 0.0001, 'netflow': -6000000, 'oi_delta': 0.03, 'rsi': 55, 'obi': 0.1},
            "expect": "APPROVED"
        },
        {
            "name": "CENÁRIO 2: Late Entry (FOMO)",
            "action": "LONG",
            "data": {'funding': 0.0001, 'netflow': -100000, 'oi_delta': 0.01, 'rsi': 80, 'obi': 0.1},
            "expect": "VETO (RSI > 75)"
        },
        {
            "name": "CENÁRIO 3: Crowded Trade (Funding Trap)",
            "action": "LONG",
            "data": {'funding': 0.0008, 'netflow': -100000, 'oi_delta': 0.05, 'rsi': 60, 'obi': 0.1},
            "expect": "VETO (Funding > 0.0005)"
        },
        {
            "name": "CENÁRIO 4: Fake Pump (Price Up, Netflow Inflow)",
            "action": "LONG",
            "data": {
                'funding': 0.0004, # High but not veto
                'netflow': 15000000, # Inflow MASSIVE (Exchange Deposit -> Dump)
                'oi_delta': 0.01,
                'rsi': 65,
                'obi': 0.0
            },
            "expect": "CAUTIOUS"
        },
        {
            "name": "CENÁRIO 5: Fighting the Wall (Liquidity Block)",
            "action": "LONG",
            "data": {'funding': 0.0001, 'netflow': -100000, 'oi_delta': 0.01, 'rsi': 50, 'obi': -0.4},
            "expect": "VETO (OBI < -0.3)"
        }
    ]

    for sc in scenarios:
        logger.info(f"--- {sc['name']} ---")
        approved, reason, size_factor = brain.validate_entry("BTC_USDC", sc['action'], sc['data'])
        status = " PASS" if approved else "️ BLOCK"
        logger.info(f"Result: {status} | SizeFactor: {size_factor} | Reason: {reason}")
        
        # Validation of expectation (simple string check)
        if (approved and "APPROVED" in sc['expect']) or \
           (approved and "CAUTIOUS" in sc['expect'] and size_factor == 0.1) or \
           (not approved and ("VETO" in sc['expect'] or "REJECTED" in sc['expect'])):
             logger.info(">> TEST RESULT: CORRECT ")
        else:
             logger.info(f">> TEST RESULT: FAILURE  (Expected {sc['expect']})")
        logger.info("")

if __name__ == "__main__":
    run_simulation()
