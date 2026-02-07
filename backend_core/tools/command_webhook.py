import os
import sys

# Adicionar caminhos para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

import logging
import asyncio
import json
from aiohttp import web
from typing import Dict, Any

from tools.vsc_transformer import VSCLayer
from tools.market_proxy_oracle import MarketProxyOracle
from tools.panic_sentinel import PanicSentinel
from tools.integrity_audit import IntegrityAudit
from core.backpack_transport import BackpackTransport
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from backpack_trade import BackpackTrade

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OBICommander")

class OBICommander:
    """
    Interface de Comando Agêntica (Jarvis Mode).
    Recebe comandos naturais/VSC via Webhook e orquestra a execução na VPS.
    """
    
    def __init__(self):
        self.vsc = VSCLayer()
        self.oracle = MarketProxyOracle(self.vsc)
        self.audit = IntegrityAudit()
        # Inicialização preguiçosa do Sentinel para não bloquear startup se credenciais faltarem
        self.sentinel = None 

    async def _get_sentinel(self):
        if not self.sentinel:
            self.sentinel = PanicSentinel()
        return self.sentinel

    async def process_command(self, raw_text: str) -> str:
        """Processa texto bruto (ex: do WhatsApp) e retorna resposta VSC"""
        cmd = raw_text.upper().strip()
        
        # 1. Parsing Básico de Intenção
        if cmd.startswith("OBI, STATUS"):
            # Ex: "OBI, STATUS SOL"
            parts = cmd.split()
            symbol = parts[2] + "_USDC" if len(parts) > 2 else "SOL_USDC"
            return await self.cmd_status(symbol)
            
        elif cmd.startswith("OBI, SNIPER"):
            # Ex: "OBI, SNIPER SOL 1000 ARROJADO"
            try:
                parts = cmd.split()
                symbol = parts[2] + "_USDC"
                qty = float(parts[3])
                profile = parts[4]
                return await self.cmd_sniper(symbol, qty, profile)
            except Exception as e:
                return f"ERR|PARSE|{str(e)}"
                
        elif cmd.startswith("OBI, PANIC"):
            # Ex: "OBI, PANIC SOL"
            parts = cmd.split()
            symbol = parts[2] + "_USDC"
            return await self.cmd_panic(symbol)

        return "ERR|UNKNOWN_COMMAND"

    async def cmd_status(self, symbol: str) -> str:
        """Retorna status do Oracle em VSC"""
        # Mocking real-time data fetch for speed, in production would query BackpackData
        # Aqui consultamos o Oracle sobre a saúde do ativo no buffer
        
        # Simular atualização do buffer (em prod isso viria do websocket)
        # self.vsc.update_scout_buffer(...) 
        
        is_healthy, reason = self.oracle.analyze_liquidity_health(symbol)
        
        # Mock OBI score e Preço (Placeholder)
        price = 0.0 # Deveria vir do cache
        obi = 0.0
        
        health_status = "LIQ:HIGH" if is_healthy else f"LIQ:LOW({reason})"
        trend = "BULL" if obi > 0 else "BEAR"
        
        return f"OBI|{symbol}|PRICE:{price}|OBI:{obi}({trend})|{health_status}"

    async def cmd_sniper(self, symbol: str, qty: float, profile: str) -> str:
        """
        Executa entrada Sniper com validação Oracle + VSC Atomic.
        """
        # 1. Oracle Vetting
        vetoed, reason = self.oracle.veto_signal(symbol, "buy", 0.5) # Mock OBI positivo
        
        if vetoed:
            return f"SNIPER|VETOED|{reason}"
            
        # 2. Validação Atômica (Simulada)
        # ...
        
        # 3. Gerar Prova de Integridade (ZK-Lite)
        trade_payload = {"symbol": symbol, "side": "Buy", "quantity": qty, "price": 0} # Mock
        oracle_context = {"obi_score": 0.5, "sentinel_active": True}
        
        proof_hash = self.audit.generate_trade_proof(trade_payload, oracle_context)
        
        # 4. Confirmação com Hash
        return f"SNIPER|CONFIRMED|{symbol}|{qty}|HASH:{proof_hash[:8]}..."

    async def cmd_panic(self, symbol: str) -> str:
        """Dispara Panic Sentinel"""
        try:
            sentinel = await self._get_sentinel()
            # Dispara em background para não bloquear o webhook
            asyncio.create_task(sentinel.atomic_panic_exit(symbol))
            return f"PANIC|INITIATED|{symbol}|CHECK_LOGS"
        except Exception as e:
            return f"PANIC|ERROR|{str(e)}"

# --- Servidor Webhook ---
async def webhook_handler(request):
    try:
        data = await request.json()
        text = data.get('text', '')
        
        commander = request.app['commander']
        response_vsc = await commander.process_command(text)
        
        return web.json_response({"reply": response_vsc})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

def start_server(port=8080):
    app = web.Application()
    app['commander'] = OBICommander()
    app.router.add_post('/webhook', webhook_handler)
    
    logger.info(f"OBI Jarvis Webhook running on port {port}")
    web.run_app(app, port=port)

if __name__ == "__main__":
    # Modo de Teste CLI Direto
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        async def test_cli():
            cmd = OBICommander()
            
            print("--- Testing Jarvis Commands ---")
            
            # 1. Status
            print(f"Input: 'OBI, status SOL'")
            res = await cmd.process_command("OBI, status SOL")
            print(f"Output: {res}\n")
            
            # 2. Sniper
            print(f"Input: 'OBI, sniper SOL 100 ARROJADO'")
            res = await cmd.process_command("OBI, sniper SOL 100 ARROJADO")
            print(f"Output: {res}\n")
            
        asyncio.run(test_cli())
    else:
        start_server()
