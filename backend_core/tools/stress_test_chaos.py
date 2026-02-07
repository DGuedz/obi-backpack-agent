import asyncio
import time
import os
import sys
import logging
from typing import List

# Adicionar caminhos para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from tools.command_webhook import OBICommander
from tools.vsc_transformer import VSCLayer

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ChaosSimulator")

class ChaosSimulator:
    """
    Simulador de Caos (Stress Test).
    Bombardeia o OBI Commander com ordens de alta frequência
    para validar latência VSC e integridade do Audit Vault.
    """
    
    def __init__(self, total_orders=50):
        self.commander = OBICommander()
        self.total_orders = total_orders
        self.results = []
        self.audit_path = "logs/audit_vault.vsc"

    async def _simulate_market_conditions(self):
        """Popula o buffer do Oracle com dados 'saudáveis' para permitir trades"""
        logger.info("Injetando liquidez simulada no Oracle...")
        # Simular 10 snapshots saudáveis para SOL_USDC
        symbol = "SOL_USDC"
        for i in range(10):
            # Spread baixo (0.01) para passar no Oracle
            mock_depth = {
                "symbol": symbol, 
                "best_bid": 145.00, 
                "best_ask": 145.01, 
                "spread": 0.01
            }
            # Update buffer via VSC layer inside commander (acessando via oracle -> vsc)
            self.commander.oracle.vsc.update_scout_buffer(symbol, mock_depth)

    async def run_fire_sprint(self):
        print(f"\n INICIANDO SPRINT DE FOGO: {self.total_orders} Ordens de Sniper ")
        print("-" * 60)
        
        # 1. Preparar Terreno
        await self._simulate_market_conditions()
        
        # Limpar ou contar linhas do vault atual
        initial_audit_count = 0
        if os.path.exists(self.audit_path):
            with open(self.audit_path, 'r') as f:
                initial_audit_count = sum(1 for line in f)
        
        start_time = time.time()
        
        # 2. Bombardeio Assíncrono
        tasks = []
        for i in range(self.total_orders):
            # Variação de quantidade para gerar hashes únicos
            qty = 10 + (i * 0.1) 
            cmd_text = f"OBI, SNIPER SOL {qty:.1f} ARROJADO"
            tasks.append(self._execute_and_measure(cmd_text, i))
            
        # Executar em paralelo (Simulando pânico de múltiplos usuários/bots ou HFT)
        self.results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # 3. Relatório de Danos
        self._generate_report(total_time, initial_audit_count)

    async def _execute_and_measure(self, cmd_text: str, idx: int) -> float:
        """Executa um comando e mede a latência"""
        t0 = time.perf_counter()
        response = await self.commander.process_command(cmd_text)
        latency_ms = (time.perf_counter() - t0) * 1000
        
        # Verificar se foi confirmado
        status = "OK" if "CONFIRMED" in response else "FAIL"
        if status == "FAIL":
            logger.warning(f"Order {idx} Failed: {response}")
            
        return latency_ms

    def _generate_report(self, total_time: float, initial_audit_count: int):
        # Contar novas linhas no audit
        final_audit_count = 0
        if os.path.exists(self.audit_path):
            with open(self.audit_path, 'r') as f:
                final_audit_count = sum(1 for line in f)
        
        new_audits = final_audit_count - initial_audit_count
        avg_latency = sum(self.results) / len(self.results)
        max_latency = max(self.results)
        min_latency = min(self.results)
        throughput = self.total_orders / total_time
        
        print("\n RELATÓRIO PÓS-AÇÃO (CHAOS REPORT)")
        print("-" * 60)
        print(f"Tempo Total de Execução: {total_time:.4f}s")
        print(f"Throughput (TPS):        {throughput:.2f} ordens/seg")
        print(f"Latência Média:          {avg_latency:.4f}ms")
        print(f"Latência Mínima:         {min_latency:.4f}ms")
        print(f"Latência Máxima:         {max_latency:.4f}ms")
        print("-" * 60)
        print(f"Auditoria Esperada:      {self.total_orders} registros")
        print(f"Auditoria Gravada:       {new_audits} registros")
        print(f"Integridade do Vault:    {' BLINDADA' if new_audits == self.total_orders else ' FALHA DE INTEGRIDADE'}")
        print("-" * 60)
        
        if avg_latency < 50:
            print(" RESULTADO: INSTITUTIONAL GRADE (TIER 3)")
        elif avg_latency < 200:
            print("️ RESULTADO: RETAIL GRADE (TIER 2)")
        else:
            print(" RESULTADO: LATÊNCIA INACEITÁVEL")

if __name__ == "__main__":
    sim = ChaosSimulator(total_orders=50)
    asyncio.run(sim.run_fire_sprint())
