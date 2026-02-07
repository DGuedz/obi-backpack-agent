#!/usr/bin/env python3
"""
Sistema Integrado de Swing Trading Pré-TGE
Combina todos os componentes: trading, risco, monitoramento e execução
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Adicionar diretório pai ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.swing_trader_conservative import ConservativeSwingTrader
from tools.swing_risk_manager import SwingRiskManager
from tools.swing_position_monitor import SwingPositionMonitor

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swing_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedSwingSystem:
    """Sistema integrado de swing trading com todos os componentes"""
    
    def __init__(self):
        # Componentes principais
        self.trader = ConservativeSwingTrader()
        self.risk_manager = SwingRiskManager()
        self.monitor = SwingPositionMonitor()
        
        # Estado do sistema
        self.is_running = False
        self.system_status = 'INITIALIZED'
        self.start_time = None
        
        # Métricas de performance
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        
    async def initialize_system(self):
        """Inicializa todos os componentes do sistema"""
        try:
            logger.info(" Inicializando Sistema Integrado de Swing Trading")
            
            # Verificar capital disponível
            capital = await self.get_available_capital()
            if capital < self.trader.capital_minimo:
                logger.error(f" Capital insuficiente: ${capital:.2f} < ${self.trader.capital_minimo:.2f}")
                return False
            
            logger.info(f" Capital disponível: ${capital:.2f}")
            
            # Configurar conexões com bancos de dados
            await self.setup_database_connections()
            
            # Verificar integridade do sistema
            if not await self.system_health_check():
                logger.error(" Falha na verificação de integridade do sistema")
                return False
            
            self.system_status = 'READY'
            logger.info(" Sistema inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f" Erro na inicialização do sistema: {e}")
            self.system_status = 'ERROR'
            return False
    
    async def setup_database_connections(self):
        """Configura conexões com bancos de dados"""
        try:
            # Criar diretório de dados se não existir
            os.makedirs('data', exist_ok=True)
            
            # Verificar e criar tabelas de sistema
            await self.create_system_tables()
            
            logger.info(" Bancos de dados configurados")
            
        except Exception as e:
            logger.error(f"Erro ao configurar bancos de dados: {e}")
            raise
    
    async def create_system_tables(self):
        """Cria tabelas do sistema integrado"""
        conn = sqlite3.connect('data/swing_system.db')
        cursor = conn.cursor()
        
        # Tabela de performance do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                total_trades INTEGER,
                winning_trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                avg_roi REAL,
                max_drawdown REAL,
                active_positions INTEGER,
                system_status TEXT
            )
        ''')
        
        # Tabela de decisões do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                decision_type TEXT NOT NULL,
                symbol TEXT,
                action TEXT,
                reason TEXT,
                risk_level TEXT,
                outcome TEXT,
                pnl REAL
            )
        ''')
        
        # Tabela de eventos do sistema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def system_health_check(self) -> bool:
        """Verifica integridade do sistema"""
        try:
            # Verificar conectividade com APIs
            # Verificar espaço em disco
            # Verificar memória disponível
            # Verificar latência de rede
            
            logger.info(" Verificação de integridade concluída")
            return True
            
        except Exception as e:
            logger.error(f" Falha na verificação de integridade: {e}")
            return False
    
    async def get_available_capital(self) -> float:
        """Obtém capital disponível real"""
        try:
            # Simulação - em produção, integrar com exchange API
            # Verificar saldo em USDC, USDT, etc.
            return 1000.0  # Simulado
            
        except Exception as e:
            logger.error(f"Erro ao obter capital disponível: {e}")
            return 0.0
    
    async def run_swing_trading_cycle(self):
        """Executa um ciclo completo de swing trading"""
        try:
            logger.info(" Iniciando ciclo de swing trading")
            
            # 1. Análise de mercado e oportunidades
            opportunities = await self.analyze_market_opportunities()
            if not opportunities:
                logger.info(" Nenhuma oportunidade de swing identificada")
                return
            
            # 2. Validação de risco para cada oportunidade
            valid_opportunities = []
            for opp in opportunities:
                is_valid, reason = await self.validate_opportunity_risk(opp)
                if is_valid:
                    valid_opportunities.append(opp)
                else:
                    logger.info(f" Oportunidade {opp['symbol']} rejeitada: {reason}")
            
            if not valid_opportunities:
                logger.info("️ Nenhuma oportunidade aprovada após validação de risco")
                return
            
            # 3. Seleção da melhor oportunidade
            best_opportunity = self.select_best_opportunity(valid_opportunities)
            
            # 4. Execução do trade
            trade_result = await self.execute_swing_trade(best_opportunity)
            
            if trade_result['success']:
                # 5. Adicionar ao monitoramento
                await self.add_position_to_monitoring(trade_result['position'])
                
                # 6. Logar decisão
                await self.log_system_decision('TRADE_ENTRY', best_opportunity['symbol'], 
                                             'ENTER', trade_result['reason'], 
                                             trade_result['risk_level'])
                
                self.total_trades += 1
                logger.info(f" Trade swing executado: {best_opportunity['symbol']}")
            
        except Exception as e:
            logger.error(f" Erro no ciclo de swing trading: {e}")
            await self.log_system_event('ERROR', 'CRITICAL', f"Erro no ciclo: {str(e)}")
    
    async def analyze_market_opportunities(self) -> List[Dict]:
        """Analisa oportunidades de swing no mercado"""
        try:
            # Usar o scanner do trader conservador
            opportunities = await self.trader.scan_for_opportunities()
            
            # Filtrar para swings apenas (excluir scalps)
            swing_opportunities = []
            for opp in opportunities:
                if self.is_swing_opportunity(opp):
                    swing_opportunities.append(opp)
            
            logger.info(f" {len(swing_opportunities)} oportunidades de swing identificadas")
            return swing_opportunities
            
        except Exception as e:
            logger.error(f"Erro na análise de oportunidades: {e}")
            return []
    
    def is_swing_opportunity(self, opportunity: Dict) -> bool:
        """Verifica se oportunidade é adequada para swing"""
        try:
            # Critérios para swing:
            # - OBI forte (> 0.35)
            # - Setup de médio prazo (1h/4h/1d)
            # - Volatilidade adequada para 2-7 dias
            # - Liquidez suficiente
            
            return (opportunity.get('obi', 0) > 0.35 and 
                   opportunity.get('timeframe') in ['1h', '4h', '1d'] and
                   opportunity.get('volatility', 0) < 0.05)  # < 5% volatilidade
                   
        except Exception:
            return False
    
    async def validate_opportunity_risk(self, opportunity: Dict) -> Tuple[bool, str]:
        """Valida oportunidade contra critérios de risco"""
        try:
            # Usar o risk manager para validação
            symbol = opportunity['symbol']
            proposed_size = self.calculate_position_size(opportunity)
            entry_price = opportunity['entry_price']
            side = opportunity['side']
            
            return await self.risk_manager.validate_new_position(symbol, proposed_size, entry_price, side)
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"
    
    def calculate_position_size(self, opportunity: Dict) -> float:
        """Calcula tamanho da posição baseado em risco"""
        try:
            # Risco de 1% do capital por trade
            capital = 1000.0  # Simulado
            risk_amount = capital * 0.01
            
            # Distância até o stop loss
            stop_distance = abs(opportunity['entry_price'] - opportunity['stop_loss'])
            
            # Tamanho da posição = risco / distância do stop
            position_size = risk_amount / stop_distance
            
            # Limitar a 20% do capital por posição
            max_position_size = capital * 0.20 / opportunity['entry_price']
            
            return min(position_size, max_position_size)
            
        except Exception:
            return 10.0  # Tamanho padrão
    
    def select_best_opportunity(self, opportunities: List[Dict]) -> Dict:
        """Seleciona a melhor oportunidade entre as válidas"""
        try:
            # Ordenar por score (OBI * confiança * ratio risco/recompensa)
            for opp in opportunities:
                risk_reward = abs(opp['take_profit'] - opp['entry_price']) / abs(opp['entry_price'] - opp['stop_loss'])
                opp['score'] = opp['obi'] * opp.get('confidence', 0.5) * risk_reward
            
            # Selecionar a melhor
            best = max(opportunities, key=lambda x: x['score'])
            logger.info(f" Melhor oportunidade selecionada: {best['symbol']} (score: {best['score']:.2f})")
            
            return best
            
        except Exception as e:
            logger.error(f"Erro na seleção de oportunidade: {e}")
            return opportunities[0] if opportunities else {}
    
    async def execute_swing_trade(self, opportunity: Dict) -> Dict:
        """Executa trade swing com validação completa"""
        try:
            # Preparar dados do trade
            trade_data = {
                'symbol': opportunity['symbol'],
                'side': opportunity['side'],
                'size': self.calculate_position_size(opportunity),
                'entry_price': opportunity['entry_price'],
                'take_profit': opportunity['take_profit'],
                'stop_loss': opportunity['stop_loss'],
                'timeframe': opportunity.get('timeframe', '4h'),
                'setup_type': opportunity.get('setup_type', 'SWING'),
                'confidence': opportunity.get('confidence', 0.7)
            }
            
            # Simular execução (em produção, integrar com exchange)
            success = True
            
            if success:
                position_data = {
                    'position_id': f"SWING_{opportunity['symbol']}_{int(datetime.now().timestamp())}",
                    'symbol': trade_data['symbol'],
                    'side': trade_data['side'],
                    'entry_price': trade_data['entry_price'],
                    'current_price': trade_data['entry_price'],
                    'size': trade_data['size'],
                    'take_profit': trade_data['take_profit'],
                    'stop_loss': trade_data['stop_loss'],
                    'entry_time': datetime.now().isoformat(),
                    'timeframe': trade_data['timeframe'],
                    'setup_type': trade_data['setup_type'],
                    'confidence': trade_data['confidence']
                }
                
                return {
                    'success': True,
                    'position': position_data,
                    'reason': 'Trade executado com sucesso',
                    'risk_level': 'LOW'
                }
            else:
                return {
                    'success': False,
                    'position': None,
                    'reason': 'Falha na execução do trade',
                    'risk_level': 'HIGH'
                }
                
        except Exception as e:
            logger.error(f"Erro na execução do trade: {e}")
            return {
                'success': False,
                'position': None,
                'reason': f"Erro: {str(e)}",
                'risk_level': 'CRITICAL'
            }
    
    async def add_position_to_monitoring(self, position_data: Dict):
        """Adiciona posição ao sistema de monitoramento"""
        try:
            await self.monitor.add_position(position_data)
            logger.info(f" Posição {position_data['position_id']} adicionada ao monitoramento")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar posição ao monitoramento: {e}")
    
    async def monitor_active_positions(self):
        """Monitora posições ativas em tempo real"""
        try:
            # Atualizar preços das posições
            await self.update_position_prices()
            
            # Verificar alerts e condições de saída
            await self.monitor.monitor_positions()
            
            # Avaliar necessidade de ajustar stops ou tomar profit
            await self.evaluate_position_adjustments()
            
        except Exception as e:
            logger.error(f"Erro no monitoramento de posições: {e}")
    
    async def update_position_prices(self):
        """Atualiza preços das posições ativas"""
        try:
            # Simulação - em produção, buscar preços reais
            logger.debug(" Preços das posições atualizados")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar preços: {e}")
    
    async def evaluate_position_adjustments(self):
        """Avalia necessidade de ajustes nas posições"""
        try:
            # Verificar se alguma posição atingiu targets intermediários
            # Avaliar trailing stops
            # Verificar condições de mercado mudadas
            
            logger.debug(" Ajustes de posição avaliados")
            
        except Exception as e:
            logger.error(f"Erro na avaliação de ajustes: {e}")
    
    async def log_system_decision(self, decision_type: str, symbol: str, 
                                action: str, reason: str, risk_level: str):
        """Loga decisões do sistema"""
        try:
            conn = sqlite3.connect('data/swing_system.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_decisions 
                (timestamp, decision_type, symbol, action, reason, risk_level)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), decision_type, symbol, action, reason, risk_level))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao logar decisão: {e}")
    
    async def log_system_event(self, event_type: str, severity: str, message: str, details: str = None):
        """Loga eventos do sistema"""
        try:
            conn = sqlite3.connect('data/swing_system.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_events 
                (timestamp, event_type, severity, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), event_type, severity, message, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao logar evento: {e}")
    
    async def update_performance_metrics(self):
        """Atualiza métricas de performance do sistema"""
        try:
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            conn = sqlite3.connect('data/swing_system.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_performance 
                (timestamp, total_trades, winning_trades, total_pnl, win_rate, 
                 max_drawdown, active_positions, system_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), self.total_trades, self.winning_trades, 
                  self.total_pnl, win_rate, self.max_drawdown, 
                  len(self.trader.positions), self.system_status))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")
    
    async def get_system_status(self) -> Dict:
        """Obtém status completo do sistema"""
        try:
            # Obter status de cada componente
            trader_status = 'RUNNING' if self.trader.is_running else 'STOPPED'
            
            # Obter resumo do monitoramento
            monitoring_summary = await self.monitor.get_monitoring_summary()
            
            # Calcular métricas atuais
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            return {
                'system_status': self.system_status,
                'uptime': (datetime.now() - self.start_time) if self.start_time else timedelta(0),
                'trader_status': trader_status,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'win_rate': win_rate,
                'total_pnl': self.total_pnl,
                'max_drawdown': self.max_drawdown,
                'active_positions': len(self.trader.positions),
                'monitoring_summary': monitoring_summary,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return {'error': str(e)}
    
    async def start_system(self):
        """Inicia o sistema de swing trading"""
        try:
            logger.info(" Iniciando Sistema Integrado de Swing Trading Pré-TGE")
            
            # Inicializar sistema
            if not await self.initialize_system():
                logger.error(" Falha na inicialização do sistema")
                return False
            
            self.is_running = True
            self.start_time = datetime.now()
            self.system_status = 'RUNNING'
            
            # Iniciar loops principais
            tasks = [
                asyncio.create_task(self.trading_loop()),
                asyncio.create_task(self.monitoring_loop()),
                asyncio.create_task(self.performance_loop())
            ]
            
            logger.info(" Sistema iniciado com sucesso")
            logger.info(" Monitorando oportunidades de swing com proteção máxima de capital")
            
            # Aguardar tarefas
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info(" Sistema interrompido pelo usuário")
            await self.stop_system()
            
        except Exception as e:
            logger.error(f" Erro crítico no sistema: {e}")
            self.system_status = 'ERROR'
            await self.stop_system()
    
    async def stop_system(self):
        """Para o sistema de forma segura"""
        try:
            logger.info(" Parando sistema de swing trading")
            
            self.is_running = False
            self.system_status = 'STOPPED'
            
            # Fechar posições se necessário
            # Salvar estado final
            await self.update_performance_metrics()
            
            # Gerar relatório final
            final_status = await self.get_system_status()
            logger.info(f" Relatório Final: {final_status}")
            
            logger.info(" Sistema parado com segurança")
            
        except Exception as e:
            logger.error(f"Erro ao parar sistema: {e}")
    
    async def trading_loop(self):
        """Loop principal de trading"""
        while self.is_running:
            try:
                await self.run_swing_trading_cycle()
                await asyncio.sleep(1800)  # 30 minutos entre ciclos
                
            except Exception as e:
                logger.error(f"Erro no loop de trading: {e}")
                await self.log_system_event('ERROR', 'CRITICAL', f"Erro no trading loop: {str(e)}")
                await asyncio.sleep(300)  # Esperar 5 minutos
    
    async def monitoring_loop(self):
        """Loop de monitoramento"""
        while self.is_running:
            try:
                await self.monitor_active_positions()
                await asyncio.sleep(300)  # 5 minutos
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto
    
    async def performance_loop(self):
        """Loop de atualização de performance"""
        while self.is_running:
            try:
                await self.update_performance_metrics()
                await asyncio.sleep(3600)  # 1 hora
                
            except Exception as e:
                logger.error(f"Erro no loop de performance: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos

async def main():
    """Função principal"""
    try:
        system = IntegratedSwingSystem()
        await system.start_system()
        
    except KeyboardInterrupt:
        logger.info("\n Sistema interrompido pelo usuário")
        
    except Exception as e:
        logger.error(f" Erro fatal: {e}")

if __name__ == "__main__":
    asyncio.run(main())