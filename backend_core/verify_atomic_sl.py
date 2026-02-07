
import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Add current directory to path to allow imports
sys.path.append(os.getcwd())

from strategies.sniper_executor import SniperExecutor

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AtomicVerifier")

async def run_verification():
    logger.info("️  INICIANDO VERIFICAÇÃO DE STOP LOSS ATÔMICO ️")
    
    # 1. Mock Transport (API Client)
    transport = MagicMock()
    transport.execute_order.return_value = {"status": "filled"} # Simula sucesso na entrada
    transport._send_request = MagicMock() # Intercepta chamadas de API genéricas (usado para SL)
    transport.get_positions.return_value = [] # Sem posições abertas

    # 2. Mock Data Client & Oracle
    data_client = MagicMock()
    
    # 3. Instantiate SniperExecutor
    # We need to mock the internal oracle of SniperExecutor or mock the data_client responses
    # It's easier to mock the oracle attribute of the executor instance directly after init
    executor = SniperExecutor(transport, data_client, risk_manager=MagicMock())
    
    # MOCK THE ORACLE COMPASS DIRECTLY
    # Simulating a PERFECT BUY SCENARIO (Score 80, Bullish)
    mock_compass = {
        'score': 80,
        'direction': 'BULLISH',
        'volatility_risk': 'LOW',
        'suggested_leverage': 10,
        'stop_loss_dist': 0.05,
        'current_price': 100.0, # Preço Simulado: $100
        'reasons': ['Mocked High Score']
    }
    
    executor.oracle.get_market_compass = MagicMock(return_value=mock_compass)
    
    # 4. Run Scan & Execute
    symbol = "SOL_USDC_PERP"
    logger.info(f" Simulando entrada em {symbol} com Score 80 (BULL)...")
    
    await executor.scan_and_execute(symbol)
    
    # 5. Verify Execution
    logger.info("\n VERIFICANDO CHAMADAS DE API...")
    
    # Check Entry Order
    transport.execute_order.assert_called()
    call_args = transport.execute_order.call_args
    logger.info(f" Ordem de Entrada Detectada: {call_args}")
    
    # Check Arguments: symbol, orderType, side, quantity
    # execute_order(symbol, "Market", side, quantity)
    args, _ = call_args
    assert args[0] == symbol
    assert args[1] == "Market"
    assert args[2] == "Buy"
    
    # Check Stop Loss Order
    # _send_request("POST", "/api/v1/order", "orderExecute", payload)
    transport._send_request.assert_called()
    sl_call_args = transport._send_request.call_args
    logger.info(f" Ordem de Stop Loss Detectada: {sl_call_args}")
    
    sl_args, _ = sl_call_args
    method, endpoint, operation, payload = sl_args
    
    assert method == "POST"
    assert endpoint == "/api/v1/order"
    assert payload['symbol'] == symbol
    assert payload['orderType'] == "StopMarket"
    assert payload['side'] == "Ask" # Stop de Long é Sell (Ask)
    
    # Verify Stop Price Logic
    # Entry was 100.0. SL dist is 0.05 (5%). Stop should be 95.0.
    trigger_price = float(payload['triggerPrice'])
    expected_sl = 100.0 * (1 - 0.05)
    
    if abs(trigger_price - expected_sl) < 0.1:
        logger.info(f" Preço de Stop Correto: {trigger_price} (Esperado: {expected_sl})")
    else:
        logger.error(f" ERRO NO CÁLCULO DE STOP: {trigger_price} != {expected_sl}")
        raise Exception("Cálculo de Stop Loss Incorreto")

    logger.info("\n RESULTADO: SISTEMA BLINDADO. STOP LOSS ATÔMICO FUNCIONAL.")

if __name__ == "__main__":
    try:
        asyncio.run(run_verification())
    except Exception as e:
        logger.error(f" FALHA NA VERIFICAÇÃO: {e}")
        sys.exit(1)
