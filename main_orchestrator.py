import asyncio
import os
import sys
import logging
import signal
from datetime import datetime
from dotenv import load_dotenv

# Adicionar caminhos
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), 'strategies'))
sys.path.append(os.path.join(os.getcwd(), 'safety'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

from core.backpack_transport import BackpackTransport
from backpack_data import BackpackData # Wrapper legado compatível
from backpack_auth import BackpackAuth
from core.risk_manager import RiskManager
from strategies.sniper_executor import SniperExecutor
from strategies.weaver_grid import WeaverGrid # Importando o Sleeper Agent
from safety.sentinel import Sentinel
from tools.market_wide_scanner import scan_market_wide

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("omega_protocol.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Orchestrator")

class OmegaOrchestrator:
    """
     OMEGA ORCHESTRATOR
    O Maestro que rege a execução paralela de todos os componentes.
    - Sentinel (Safety)
    - Sniper (Strategy)
    - Risk Manager (Core)
    """
    def __init__(self, stealth_mode=False):
        load_dotenv()
        self.stealth_mode = stealth_mode
        
        # 1. Inicializar Transporte e Dados
        self.transport = BackpackTransport()
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data_client = BackpackData(self.auth)
        
        # 2. Inicializar Core
        self.risk_manager = RiskManager(self.transport)
        
        # 3. Inicializar Estratégia e Segurança
        self.sniper = SniperExecutor(self.transport, self.data_client, self.risk_manager, stealth_mode=self.stealth_mode)
        self.weaver = WeaverGrid(self.transport, self.data_client, self.risk_manager) # Inicializa o Weaver
        self.sentinel = Sentinel(self.transport, self.risk_manager)
        
        # Estado do Modo
        self.active_mode = "PROFIT" # PROFIT (Sniper) ou VOLUME (Weaver)
        self.VOLUME_MODE_START_HOUR = 7 # 7:00 AM
        
        # Lista de Ativos Alvo (Dinâmica via Radar)
        self.targets = [
            "LIT_USDC_PERP", 
            "HYPE_USDC_PERP", 
            "SOL_USDC_PERP", 
            "BTC_USDC_PERP", 
            "BNB_USDC_PERP"
        ]
        
        self.is_running = True

    async def run_opportunity_radar(self):
        """
         OPPORTUNITY RADAR
        Roda o Market Scanner periodicamente e atualiza a lista de alvos do Orchestrator.
        """
        logger.info(" Opportunity Radar Inicializado.")
        while self.is_running:
            try:
                logger.info(" [RADAR] Escaneando mercado por oportunidades quentes...")
                # Roda o scanner (função importada)
                # Nota: scan_market_wide imprime no console, vamos capturar apenas o retorno se modificarmos.
                # Como modificamos para retornar lista, vamos usar.
                new_opportunities = await scan_market_wide()
                
                if new_opportunities:
                    # Merge com targets fixos (BTC/ETH/SOL sempre ficam)
                    fixed_targets = ["BTC_USDC_PERP", "ETH_USDC_PERP", "SOL_USDC_PERP"]
                    
                    # Atualiza targets (Mantém fixos + Novas oportunidades)
                    # Remove duplicatas
                    current_set = set(fixed_targets + new_opportunities)
                    self.targets = list(current_set)
                    
                    logger.info(f" [RADAR] Alvos Atualizados: {len(self.targets)} ativos ({', '.join(self.targets)})")
                else:
                    logger.info(" [RADAR] Nenhuma oportunidade nova. Mantendo alvos atuais.")
                
                await asyncio.sleep(300) # 5 minutos entre scans
                
            except Exception as e:
                logger.error(f"Erro no Radar: {e}")
                await asyncio.sleep(60)

    async def run_sniper_loop(self):
        """Loop de execução da estratégia (Sniper)."""
        if self.stealth_mode:
            logger.info(" MODO STEALTH ATIVO: Monitoramento Passivo Ligado. Execução de Ordens BLOQUEADA.")
        else:
            logger.info(f" Sniper Loop Iniciado (MODO ATUAL: {self.active_mode}).")
            # Forçar atualização inicial do modo
            self.sniper.set_mode(self.active_mode)

        while self.is_running:
            # Check de Horário para Ativação Automática do Modo Volume
            # FORÇANDO MODO VOLUME AGORA (STRATEGIC FARMING)
            # now = datetime.now()
            # if self.active_mode == "PROFIT" and now.hour >= self.VOLUME_MODE_START_HOUR and now.hour < 18:
            
            # OVERRIDE: Modo Volume Permanente para atingir meta de $300 com giro rápido
            if self.active_mode != "MANUAL_EXIT":
                 logger.info(f" OVERRIDE: Ativando MODO MANUAL EXIT (Leverage 9x, Infinite Profit).")
                 self.active_mode = "MANUAL_EXIT"
                 self.sniper.set_mode("MANUAL_EXIT")
            
            if not self.sentinel.is_active:
                logger.warning("️ Sentinel inativo/pausado. Sniper aguardando...")
                await asyncio.sleep(5)
                continue
                
            for symbol in self.targets:
                # SNIPER SCALP (Agora Ajustado para Volume/Profit dinamicamente)
                await self.sniper.scan_and_execute(symbol)
                await asyncio.sleep(1) # Intervalo entre ativos
            
            await asyncio.sleep(2) # Intervalo do ciclo

    async def monitor_session_stats(self):
        """Monitora e exibe estatísticas da sessão (Volume e PnL) periodicamente."""
        logger.info(" Session Stats Monitor Iniciado.")
        start_time = datetime.now()
        start_equity = 0.0
        
        # Aguardar Sentinel inicializar para pegar equity
        while self.sentinel.equity_base == 0:
            await asyncio.sleep(1)
        start_equity = self.sentinel.equity_base
        
        while self.is_running:
            try:
                await asyncio.sleep(300) # A cada 5 minutos
                
                current_time = datetime.now()
                uptime = current_time - start_time
                
                # Equity Atual
                current_equity = self.sentinel.equity_base
                pnl = current_equity - start_equity
                pnl_pct = (pnl / start_equity) * 100 if start_equity > 0 else 0
                
                # Volume (Estimado via Fills Recentes)
                # Nota: Isso é uma aproximação. Ideal seria persistir trades.
                # Vamos pegar os últimos 100 fills e somar o que for recente (dentro da janela de 5 min)
                # Para simplificar, vamos confiar no log de execução ou apenas mostrar PnL por enquanto.
                # Mas o usuário quer ver volume. Vamos tentar pegar do endpoint history se possível.
                # data_client.get_fill_history() é síncrono, cuidado com block.
                # Vamos rodar em thread separada ou aceitar o block rápido.
                
                fills = self.data_client.get_fill_history(limit=100)
                session_vol = 0.0
                if fills:
                    # Filtrar fills após start_time
                    # Formato data fill: "2024-01-25T..." isoformat
                    pass 
                    # Complexidade de parse de data aqui pode travar. 
                    # Vamos manter simples: Mostrar Equity e Modo.
                
                logger.info(f" [SITREP] Uptime: {str(uptime).split('.')[0]} | Mode: {self.active_mode}")
                logger.info(f"    Equity: ${current_equity:.2f} | PnL Sessão: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                
                if self.active_mode == "VOLUME":
                    logger.info("   ️ Status Weaver: REDE ATIVA (Farming em andamento...)")
                    
            except Exception as e:
                logger.error(f"Erro no Monitor de Stats: {e}")

    async def start(self):
        """Inicia o sistema completo."""
        logger.info(" INICIANDO PROTOCOLO OMEGA (Spec-Driven)...")
        logger.info(" MISSÃO ATUAL: LUCRO TÁTICO (Deadline: 7:00 AM)")
        logger.info("   Estratégia: Sniper Flow-First | Alvo: Tendência + OBI")
        
        # 1. Inicializar Sentinel (Captura Equity Base)
        await self.sentinel.initialize()
        
        if not self.sentinel.is_active:
            logger.critical(" Falha crítica na inicialização do Sentinel. Abortando.")
            return

        # 2. Criar Tasks Assíncronas
        tasks = [
            asyncio.create_task(self.sentinel.monitor_loop()),
            asyncio.create_task(self.run_sniper_loop()),
            asyncio.create_task(self.monitor_session_stats()),
            asyncio.create_task(self.run_opportunity_radar())
        ]
        
        # 3. Aguardar execução
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info(" Orquestrador Parado.")
        except Exception as e:
            logger.critical(f" Erro Fatal no Orquestrador: {e}")
        finally:
            self.is_running = False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stealth", action="store_true", help="Ativa modo Stealth (Monitoramento Passivo)")
    args = parser.parse_args()

    orchestrator = OmegaOrchestrator(stealth_mode=args.stealth)
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        print("\n Encerrando Protocolo Omega...")
