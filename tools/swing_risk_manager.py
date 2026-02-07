#!/usr/bin/env python3
"""
Sistema de Gerenciamento de Risco para Swing Trading Pré-TGE
Foco: Proteção absoluta do capital com regras específicas para trades de médio prazo
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sqlite3
import numpy as np

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swing_risk_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Métricas de risco para uma posição"""
    position_id: str
    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    size: float
    side: str
    entry_time: datetime
    max_drawdown: float
    volatility_24h: float
    correlation_risk: float
    liquidity_risk: float
    
class SwingRiskManager:
    """Gerenciador de Risco para Swing Trading Pré-TGE"""
    
    def __init__(self):
        # Limites de risco ultra-conservadores
        self.max_portfolio_risk = 0.03        # 3% risco total do portfólio
        self.max_single_position_risk = 0.01  # 1% risco por posição
        self.max_daily_loss = 0.02            # 2% perda máxima diária
        self.max_drawdown_allowed = 0.05     # 5% drawdown máximo
        
        # Limites de exposição
        self.max_positions = 3                # Máximo 3 posições
        self.max_correlation = 0.7             # Correlação máxima entre posições
        self.min_liquidity_ratio = 0.1         # Ratio mínimo de liquidez
        
        # Limites de tempo para swing
        self.min_holding_time = 1              # Mínimo 1 dia
        self.max_holding_time = 7              # Máximo 7 dias
        self.early_exit_threshold = 0.02     # 2% para saída antecipada
        
        # Buffers de segurança
        self.stop_loss_buffer = 0.005          # 0.5% buffer no stop
        self.take_profit_buffer = 0.002      # 0.2% buffer no TP
        self.volatility_multiplier = 1.5     # Multiplicador para volatilidade alta
        
        self.db_path = 'data/swing_risk.db'
        self.setup_database()
        
    def setup_database(self):
        """Configura banco de dados para tracking de risco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                symbol TEXT,
                position_id TEXT,
                risk_metric REAL,
                threshold REAL,
                action_taken TEXT,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                total_exposure REAL,
                portfolio_risk_pct REAL,
                correlation_risk REAL,
                liquidity_risk REAL,
                var_95 REAL,
                var_99 REAL,
                max_drawdown REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def validate_new_position(self, symbol: str, proposed_size: float, 
                                   entry_price: float, side: str) -> Tuple[bool, str]:
        """Valida se nova posição atende aos critérios de risco"""
        try:
            # 1. Verificar exposição total
            current_exposure = await self.calculate_total_exposure()
            proposed_exposure = proposed_size * entry_price
            total_exposure = current_exposure + proposed_exposure
            
            if total_exposure > 1000:  # Limite de exposição total (exemplo)
                return False, f"Exposição total ${total_exposure:.2f} excede limite"
            
            # 2. Verificar risco da posição
            position_risk = await self.calculate_position_risk(symbol, entry_price, side)
            if position_risk > self.max_single_position_risk:
                return False, f"Risco da posição {position_risk*100:.1f}% excede limite de {self.max_single_position_risk*100:.1f}%"
            
            # 3. Verificar correlação com posições existentes
            correlation_risk = await self.calculate_correlation_risk(symbol)
            if correlation_risk > self.max_correlation:
                return False, f"Correlação {correlation_risk*100:.1f}% excede limite de {self.max_correlation*100:.1f}%"
            
            # 4. Verificar liquidez
            liquidity_risk = await self.calculate_liquidity_risk(symbol, proposed_size)
            if liquidity_risk < self.min_liquidity_ratio:
                return False, f"Liquidez insuficiente: ratio {liquidity_risk*100:.1f}% < {self.min_liquidity_ratio*100:.1f}%"
            
            # 5. Verificar volatilidade
            volatility = await self.get_volatility_metrics(symbol)
            if volatility['current'] > volatility['threshold'] * self.volatility_multiplier:
                return False, f"Volatilidade {volatility['current']*100:.1f}% muito alta"
            
            # 6. Verificar condições de mercado
            market_conditions = await self.assess_market_conditions(symbol)
            if not market_conditions['safe_for_entry']:
                return False, f"Condições de mercado inadequadas: {market_conditions['reason']}"
            
            logger.info(f" Nova posição {symbol} validada com sucesso")
            return True, "Posição aprovada"
            
        except Exception as e:
            logger.error(f"Erro na validação de risco: {e}")
            return False, f"Erro na validação: {str(e)}"
    
    async def monitor_position_risk(self, position_id: str, symbol: str, 
                                   current_price: float, entry_price: float, 
                                   size: float, side: str) -> Dict:
        """Monitora risco de posição em tempo real"""
        try:
            metrics = RiskMetrics(
                position_id=position_id,
                symbol=symbol,
                entry_price=entry_price,
                current_price=current_price,
                stop_loss=entry_price * 0.98 if side == 'long' else entry_price * 1.02,
                take_profit=entry_price * 1.05 if side == 'long' else entry_price * 0.95,
                size=size,
                side=side,
                entry_time=datetime.now(),
                max_drawdown=await self.calculate_max_drawdown(position_id),
                volatility_24h=await self.get_24h_volatility(symbol),
                correlation_risk=await self.calculate_correlation_risk(symbol),
                liquidity_risk=await self.calculate_liquidity_risk(symbol, size)
            )
            
            # Verificar alertas de risco
            alerts = self.check_risk_alerts(metrics)
            
            if alerts:
                for alert in alerts:
                    logger.warning(f" ALERTA DE RISCO: {alert}")
                    await self.log_risk_event('ALERT', symbol, position_id, alert)
            
            return {
                'metrics': metrics,
                'alerts': alerts,
                'risk_level': self.calculate_overall_risk_level(metrics),
                'recommended_action': self.get_recommended_action(metrics, alerts)
            }
            
        except Exception as e:
            logger.error(f"Erro no monitoramento de risco: {e}")
            return {'error': str(e)}
    
    def check_risk_alerts(self, metrics: RiskMetrics) -> List[str]:
        """Verifica alertas de risco"""
        alerts = []
        
        # 1. Drawdown alert
        if metrics.max_drawdown > self.max_drawdown_allowed:
            alerts.append(f"Drawdown {metrics.max_drawdown*100:.1f}% excede limite {self.max_drawdown_allowed*100:.1f}%")
        
        # 2. Volatility alert
        if metrics.volatility_24h > 0.05:  # 5% volatilidade
            alerts.append(f"Volatilidade elevada: {metrics.volatility_24h*100:.1f}%")
        
        # 3. Liquidity alert
        if metrics.liquidity_risk < self.min_liquidity_ratio:
            alerts.append(f"Risco de liquidez: {metrics.liquidity_risk*100:.1f}%")
        
        # 4. Correlation alert
        if metrics.correlation_risk > self.max_correlation:
            alerts.append(f"Risco de correlação: {metrics.correlation_risk*100:.1f}%")
        
        # 5. Time-based alert
        holding_hours = (datetime.now() - metrics.entry_time).total_seconds() / 3600
        if holding_hours > self.max_holding_time * 24:
            alerts.append(f"Tempo máximo de holding excedido: {holding_hours/24:.1f} dias")
        
        return alerts
    
    def calculate_overall_risk_level(self, metrics: RiskMetrics) -> str:
        """Calcula nível geral de risco"""
        risk_score = 0
        
        # Fatores de risco ponderados
        if metrics.max_drawdown > 0.03: risk_score += 3
        elif metrics.max_drawdown > 0.02: risk_score += 2
        elif metrics.max_drawdown > 0.01: risk_score += 1
        
        if metrics.volatility_24h > 0.05: risk_score += 2
        elif metrics.volatility_24h > 0.03: risk_score += 1
        
        if metrics.liquidity_risk < 0.05: risk_score += 2
        elif metrics.liquidity_risk < 0.08: risk_score += 1
        
        if metrics.correlation_risk > 0.8: risk_score += 2
        elif metrics.correlation_risk > 0.6: risk_score += 1
        
        # Classificar nível de risco
        if risk_score >= 7: return 'CRITICAL'
        elif risk_score >= 5: return 'HIGH'
        elif risk_score >= 3: return 'MEDIUM'
        else: return 'LOW'
    
    def get_recommended_action(self, metrics: RiskMetrics, alerts: List[str]) -> str:
        """Recomenda ação baseada em risco"""
        risk_level = self.calculate_overall_risk_level(metrics)
        
        if risk_level == 'CRITICAL':
            return 'CLOSE_IMMEDIATELY'
        elif risk_level == 'HIGH':
            return 'REDUCE_SIZE_OR_CLOSE'
        elif risk_level == 'MEDIUM':
            return 'MONITOR_CLOSELY'
        else:
            return 'HOLD'
    
    async def calculate_portfolio_risk(self) -> Dict:
        """Calcula risco total do portfólio"""
        try:
            # Obter todas as posições
            positions = await self.get_all_positions()
            
            if not positions:
                return {
                    'total_exposure': 0,
                    'portfolio_risk_pct': 0,
                    'var_95': 0,
                    'var_99': 0,
                    'max_drawdown': 0,
                    'risk_level': 'LOW'
                }
            
            # Calcular exposição total
            total_exposure = sum(pos['size'] * pos['current_price'] for pos in positions)
            
            # Calcular VaR (Value at Risk)
            var_95 = self.calculate_var(positions, 0.95)
            var_99 = self.calculate_var(positions, 0.99)
            
            # Calcular risco de portfólio
            portfolio_risk = self.calculate_portfolio_risk_percentage(positions)
            
            # Calcular drawdown máximo
            max_drawdown = max(pos['max_drawdown'] for pos in positions) if positions else 0
            
            # Determinar nível de risco
            risk_level = self.determine_portfolio_risk_level(portfolio_risk, var_95, max_drawdown)
            
            # Logar métricas
            await self.log_portfolio_risk(total_exposure, portfolio_risk, var_95, var_99, max_drawdown)
            
            return {
                'total_exposure': total_exposure,
                'portfolio_risk_pct': portfolio_risk,
                'var_95': var_95,
                'var_99': var_99,
                'max_drawdown': max_drawdown,
                'risk_level': risk_level,
                'positions_count': len(positions)
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular risco do portfólio: {e}")
            return {'error': str(e)}
    
    def calculate_var(self, positions: List[Dict], confidence: float) -> float:
        """Calcula Value at Risk"""
        try:
            # Simulação simplificada de retornos
            returns = []
            for pos in positions:
                # Gerar retornos simulados baseados em volatilidade
                volatility = pos.get('volatility_24h', 0.02)
                current_value = pos['size'] * pos['current_price']
                
                # Simular 1000 cenários
                for _ in range(1000):
                    random_return = np.random.normal(0, volatility)
                    returns.append(current_value * random_return)
            
            if not returns:
                return 0.0
            
            # Calcular VaR
            var_percentile = (1 - confidence) * 100
            var_value = np.percentile(returns, var_percentile)
            
            return abs(var_value)
            
        except Exception:
            return 0.0
    
    def determine_portfolio_risk_level(self, portfolio_risk: float, var_95: float, max_drawdown: float) -> str:
        """Determina nível de risco do portfólio"""
        if portfolio_risk > 0.05 or var_95 > 100 or max_drawdown > 0.05:
            return 'CRITICAL'
        elif portfolio_risk > 0.03 or var_95 > 50 or max_drawdown > 0.03:
            return 'HIGH'
        elif portfolio_risk > 0.01 or var_95 > 25 or max_drawdown > 0.02:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    async def emergency_risk_check(self) -> bool:
        """Verificação de risco de emergência"""
        try:
            portfolio_risk = await self.calculate_portfolio_risk()
            
            if portfolio_risk['risk_level'] == 'CRITICAL':
                logger.critical(" RISCO CRÍTICO DETECTADO - EMERGENCY PROTOCOL")
                await self.log_risk_event('EMERGENCY', 'PORTFOLIO', 'ALL', 'Risk level CRITICAL')
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro na verificação de emergência: {e}")
            return False
    
    async def log_risk_event(self, event_type: str, symbol: str, position_id: str, description: str):
        """Loga evento de risco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_events 
                (timestamp, event_type, symbol, position_id, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), event_type, symbol, position_id, description))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao logar evento de risco: {e}")
    
    async def log_portfolio_risk(self, total_exposure: float, portfolio_risk: float, 
                                var_95: float, var_99: float, max_drawdown: float):
        """Loga métricas de risco do portfólio"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO portfolio_risk 
                (timestamp, total_exposure, portfolio_risk_pct, var_95, var_99, max_drawdown)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), total_exposure, portfolio_risk, var_95, var_99, max_drawdown))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao logar risco do portfólio: {e}")
    
    # Funções auxiliares (simplificadas)
    async def calculate_total_exposure(self) -> float:
        """Calcula exposição total atual"""
        return 500.0  # Simulado
    
    async def calculate_position_risk(self, symbol: str, entry_price: float, side: str) -> float:
        """Calcula risco de posição proposta"""
        return 0.008  # Simulado: 0.8%
    
    async def calculate_correlation_risk(self, symbol: str) -> float:
        """Calcula risco de correlação"""
        return 0.3  # Simulado
    
    async def calculate_liquidity_risk(self, symbol: str, size: float) -> float:
        """Calcula risco de liquidez"""
        return 0.15  # Simulado
    
    async def get_volatility_metrics(self, symbol: str) -> Dict:
        """Obtém métricas de volatilidade"""
        return {'current': 0.02, 'threshold': 0.025}  # Simulado
    
    async def assess_market_conditions(self, symbol: str) -> Dict:
        """Avalia condições de mercado"""
        return {'safe_for_entry': True, 'reason': 'OK'}  # Simulado
    
    async def get_all_positions(self) -> List[Dict]:
        """Obtém todas as posições"""
        return []  # Simulado
    
    def calculate_portfolio_risk_percentage(self, positions: List[Dict]) -> float:
        """Calcula risco percentual do portfólio"""
        return 0.015  # Simulado: 1.5%
    
    async def calculate_max_drawdown(self, position_id: str) -> float:
        """Calcula máximo drawdown para posição"""
        return 0.01  # Simulado
    
    async def get_24h_volatility(self, symbol: str) -> float:
        """Obtém volatilidade 24h"""
        return 0.025  # Simulado

async def main():
    """Função principal de teste"""
    risk_manager = SwingRiskManager()
    
    # Testar validação de nova posição
    is_valid, reason = await risk_manager.validate_new_position('SOL-USDC', 10.0, 50.0, 'long')
    logger.info(f"Validação de posição: {is_valid} - {reason}")
    
    # Testar risco do portfólio
    portfolio_risk = await risk_manager.calculate_portfolio_risk()
    logger.info(f"Risco do portfólio: {portfolio_risk}")

if __name__ == "__main__":
    asyncio.run(main())