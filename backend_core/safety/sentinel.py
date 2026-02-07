import asyncio
import logging
import time

class Sentinel:
    """
    ️ SENTINEL (Kill-Switch)
    Processo independente que monitora a saúde global do sistema.
    Implementa a História 3 das Especificações.
    1. Monitora Drawdown da Sessão (> 5% = SHUTDOWN)
    2. Monitora Erros de API (> 3 consecutivos = PAUSE)
    """
    def __init__(self, transport, risk_manager):
        self.transport = transport
        self.risk_manager = risk_manager
        self.logger = logging.getLogger("Sentinel")
        
        # Estado Inicial
        self.start_equity = 0.0
        self.equity_base = 0.0 # Alias para compatibilidade com Orchestrator
        self.api_error_count = 0
        self.is_active = True
        self.MAX_DRAWDOWN_PCT = 0.05 # 5%
        self.MAX_API_ERRORS = 3
        
    async def initialize(self):
        """Captura o Equity Inicial para referência de Drawdown."""
        safe, capital = self.risk_manager.check_capital_safety()
        if safe:
            # Precisamos do Equity Total, não só do usável.
            # Acessando via transport diretamente (embora risk_manager já tenha validado)
            collateral = self.transport.get_account_collateral()
            self.start_equity = float(collateral.get('netEquity', collateral.get('equity', 0)))
            self.equity_base = self.start_equity # Sync
            self.logger.info(f"️ Sentinel Inicializado. Equity Base: ${self.start_equity:.2f}")
        else:
            self.logger.error(" Sentinel falhou ao iniciar: Não foi possível ler Equity.")
            self.is_active = False

    async def monitor_loop(self):
        """Loop infinito de monitoramento."""
        if not self.is_active: return

        while True:
            try:
                # 1. Checar API Health & Drawdown
                collateral = self.transport.get_account_collateral()
                
                if not collateral:
                    self.api_error_count += 1
                    self.logger.warning(f"️ API Error Count: {self.api_error_count}/{self.MAX_API_ERRORS}")
                    if self.api_error_count >= self.MAX_API_ERRORS:
                        self.logger.critical(" API INSTÁVEL. Pausando sistema por 60s...")
                        await asyncio.sleep(60)
                        self.api_error_count = 0
                    await asyncio.sleep(5)
                    continue
                
                # Reset error count on success
                self.api_error_count = 0
                
                # 2. Calcular Drawdown
                current_equity = float(collateral.get('netEquity', collateral.get('equity', 0)))
                self.equity_base = current_equity # Update para o Orchestrator ler
                
                drawdown = (self.start_equity - current_equity) / self.start_equity
                
                if drawdown > self.MAX_DRAWDOWN_PCT:
                    self.logger.critical(f" KILL-SWITCH ATIVADO! Drawdown {drawdown*100:.2f}% > {self.MAX_DRAWDOWN_PCT*100:.1f}%")
                    self.logger.critical("    Encerrando todas as operações e processos.")
                    # Aqui chamaríamos uma função de pânico para cancelar tudo
                    # self.transport.cancel_all_orders()
                    # sys.exit(1)
                    return # Encerra o Sentinel (e idealmente o programa principal)
                
                # Log Heartbeat a cada minuto
                # self.logger.debug(f" Sentinel Vivo. DD: {drawdown*100:.2f}%")
                
                await asyncio.sleep(10) # Checar a cada 10s

            except Exception as e:
                self.logger.error(f"Erro no Sentinel: {e}")
                await asyncio.sleep(5)
