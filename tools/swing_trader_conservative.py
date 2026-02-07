#!/usr/bin/env python3
"""
Swing Trader Conservador - Estratégia de Médio Prazo para TGE
Foco: Trades seguros com holding 2-7 dias, proteção absoluta do capital
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiohttp
import pandas as pd
from dataclasses import dataclass
import sqlite3
import signal
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swing_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SwingPosition:
    """Representa uma posição swing"""
    symbol: str
    side: str  # 'long' ou 'short'
    entry_price: float
    entry_time: datetime
    size: float
    target_price: float
    stop_loss: float
    timeframe: str
    setup_type: str
    confidence: float
    max_hold_days: int = 7
    
class ConservativeSwingTrader:
    """Trader Swing Ultra-Conservador para preparação TGE"""
    
    def __init__(self):
        self.capital_minimo = 100  # USD mínimo para operar
        self.max_positions = 3     # Máximo 3 posições simultâneas
        self.risk_per_trade = 0.01 # 1% risco por trade (ultra conservador)
        self.target_roi = 0.03     # 3% target por trade
        self.stop_loss = 0.015     # 1.5% stop loss
        
        # Filtros ultra-conservadores
        self.min_volume_24h = 10_000_000  # Volume mínimo
        self.min_market_cap = 100_000_000  # Market cap mínimo
        self.min_obligation_ratio = 0.3     # OBR mínimo
        self.max_funding_rate = 0.01        # Funding rate máximo
        
        # Timeframes para análise
        self.timeframes = ['1h', '4h', '1d']
        
        self.positions: List[SwingPosition] = []
        self.closed_positions: List[SwingPosition] = []
        self.db_path = 'data/swing_trades.db'
        
        # Estado do trader
        self.is_running = False
        self.last_analysis_time = None
        
        self.setup_database()
        
    def setup_database(self):
        """Configura banco de dados para tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swing_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                exit_price REAL,
                exit_time TIMESTAMP,
                size REAL NOT NULL,
                pnl REAL,
                roi REAL,
                holding_days INTEGER,
                setup_type TEXT,
                confidence REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def get_available_capital(self) -> float:
        """Obtém capital disponível"""
        try:
            # Implementar chamada à API da exchange
            # Por enquanto, valor simulado baseado em configurações anteriores
            return 500.0  # USD
        except Exception as e:
            logger.error(f"Erro ao obter capital: {e}")
            return 0.0
            
    async def scan_swing_opportunities(self) -> List[Dict]:
        """Escaneia oportunidades de swing trading"""
        opportunities = []
        
        try:
            # Obter símbolos com volume adequado
            symbols = await self.get_high_volume_symbols()
            
            for symbol in symbols[:20]:  # Analisar top 20
                analysis = await self.analyze_swing_setup(symbol)
                if analysis and analysis['score'] >= 0.7:  # Alta confiança
                    opportunities.append(analysis)
                    
            # Ordenar por score de confiança
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f" {len(opportunities)} oportunidades swing encontradas")
            return opportunities
            
        except Exception as e:
            logger.error(f"Erro ao escanear oportunidades: {e}")
            return []
            
    async def get_high_volume_symbols(self) -> List[str]:
        """Obtém símbolos com alto volume"""
        # Implementar chamada à API
        # Por enquanto, lista baseada em tokens estabelecidos
        return [
            'SOL-USDC', 'ETH-USDC', 'BTC-USDC', 'JUP-USDC', 
            'RNDR-USDC', 'HNT-USDC', 'ORCA-USDC', 'MNGO-USDC'
        ]
        
    async def analyze_swing_setup(self, symbol: str) -> Optional[Dict]:
        """Analisa setup de swing para um símbolo"""
        try:
            # Obter dados de múltiplos timeframes
            market_data = await self.get_multi_timeframe_data(symbol)
            
            if not market_data:
                return None
                
            # Análise técnica conservadora
            technical_score = await self.conservative_technical_analysis(market_data)
            
            # Análise de sentimento/funding
            sentiment_score = await self.analyze_market_sentiment(symbol)
            
            # Análise de volume e liquidez
            liquidity_score = self.analyze_liquidity_conditions(market_data)
            
            # Score final
            total_score = (technical_score * 0.5 + sentiment_score * 0.3 + liquidity_score * 0.2)
            
            if total_score >= 0.7:
                setup_type = self.identify_setup_type(market_data)
                
                return {
                    'symbol': symbol,
                    'score': total_score,
                    'setup_type': setup_type,
                    'technical_score': technical_score,
                    'sentiment_score': sentiment_score,
                    'liquidity_score': liquidity_score,
                    'entry_price': self.calculate_entry_price(market_data, setup_type),
                    'target_price': self.calculate_target_price(market_data, setup_type),
                    'stop_loss': self.calculate_stop_loss(market_data, setup_type),
                    'risk_reward': self.calculate_risk_reward(market_data, setup_type),
                    'confidence': total_score,
                    'timeframes': market_data
                }
                
        except Exception as e:
            logger.error(f"Erro ao analisar {symbol}: {e}")
            return None
            
    async def conservative_technical_analysis(self, data: Dict) -> float:
        """Análise técnica ultra-conservadora"""
        score = 0.0
        
        try:
            # Verificar tendência de longo prazo (1D)
            daily_trend = self.analyze_trend_direction(data['1d'])
            
            # Verificar momentum no 4H
            momentum_4h = self.analyze_momentum(data['4h'])
            
            # Verificar suportes/resistências claros
            sr_levels = self.identify_support_resistance(data)
            
            # Verificar padrões de reversão confiáveis
            patterns = self.detect_reversal_patterns(data)
            
            # Pontuação baseada em múltiplos fatores
            if daily_trend in ['bullish', 'bearish']:
                score += 0.3
                
            if momentum_4h in ['oversold_bullish', 'overbought_bearish']:
                score += 0.3
                
            if len(sr_levels) >= 2:
                score += 0.2
                
            if patterns:
                score += 0.2
                
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Erro na análise técnica: {e}")
            return 0.0
            
    def identify_setup_type(self, data: Dict) -> str:
        """Identifica tipo de setup"""
        # Lógica para identificar: reversal, breakout, retracement, etc.
        return "reversal"  # Simplificado
        
    def calculate_entry_price(self, data: Dict, setup: str) -> float:
        """Calcula preço de entrada"""
        # Lógica baseada no setup
        return 50.0  # Simplificado
        
    def calculate_target_price(self, data: Dict, setup: str) -> float:
        """Calcula preço alvo (3% ROI)"""
        entry = self.calculate_entry_price(data, setup)
        return entry * (1 + self.target_roi)
        
    def calculate_stop_loss(self, data: Dict, setup: str) -> float:
        """Calcula stop loss (1.5% perda)"""
        entry = self.calculate_entry_price(data, setup)
        return entry * (1 - self.stop_loss)
        
    def calculate_risk_reward(self, data: Dict, setup: str) -> float:
        """Calcula ratio risco/recompensa"""
        entry = self.calculate_entry_price(data, setup)
        target = self.calculate_target_price(data, setup)
        stop = self.calculate_stop_loss(data, setup)
        
        reward = abs(target - entry)
        risk = abs(entry - stop)
        
        return reward / risk if risk > 0 else 0
        
    async def execute_swing_trade(self, opportunity: Dict) -> bool:
        """Executa trade swing"""
        try:
            # Verificar condições de risco
            if not await self.validate_risk_conditions(opportunity):
                return False
                
            # Calcular tamanho da posição
            position_size = self.calculate_position_size(opportunity)
            
            # Criar posição
            position = SwingPosition(
                symbol=opportunity['symbol'],
                side='long' if opportunity['setup_type'] in ['reversal', 'breakout'] else 'short',
                entry_price=opportunity['entry_price'],
                entry_time=datetime.now(),
                size=position_size,
                target_price=opportunity['target_price'],
                stop_loss=opportunity['stop_loss'],
                timeframe='4h',
                setup_type=opportunity['setup_type'],
                confidence=opportunity['confidence']
            )
            
            self.positions.append(position)
            
            logger.info(f" NOVA POSIÇÃO SWING: {position.symbol}")
            logger.info(f"    Entry: ${position.entry_price:.4f}")
            logger.info(f"    Target: ${position.target_price:.4f} ({self.target_roi*100:.1f}%)")
            logger.info(f"   ️ Stop: ${position.stop_loss:.4f} ({self.stop_loss*100:.1f}%)")
            logger.info(f"   ️ Size: {position.size:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar trade: {e}")
            return False
            
    async def validate_risk_conditions(self, opp: Dict) -> bool:
        """Valida condições de risco"""
        try:
            # Verificar número de posições abertas
            if len(self.positions) >= self.max_positions:
                logger.warning(f" Máximo de posições atingido: {self.max_positions}")
                return False
                
            # Verificar capital disponível
            capital = await self.get_available_capital()
            if capital < self.capital_minimo:
                logger.warning(f" Capital insuficiente: ${capital:.2f}")
                return False
                
            # Verificar risco/recompensa mínimo
            if opp['risk_reward'] < 1.5:  # Mínimo 1.5:1
                logger.warning(f" Risco/recompensa baixo: {opp['risk_reward']:.2f}")
                return False
                
            # Verificar confiança mínima
            if opp['confidence'] < 0.7:
                logger.warning(f" Confiança baixa: {opp['confidence']:.2f}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Erro na validação de risco: {e}")
            return False
            
    def calculate_position_size(self, opportunity: Dict) -> float:
        """Calcula tamanho da posição baseado em risco"""
        try:
            # Risco baseado em % do capital
            capital = 500  # Capital simulado
            risk_amount = capital * self.risk_per_trade
            
            # Calcular tamanho baseado em stop loss
            entry = opportunity['entry_price']
            stop = opportunity['stop_loss']
            risk_per_unit = abs(entry - stop)
            
            if risk_per_unit > 0:
                size = risk_amount / risk_per_unit
                return min(size, capital * 0.1)  # Máximo 10% do capital por trade
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho: {e}")
            return 0.0
            
    async def monitor_positions(self):
        """Monitora posições abertas"""
        try:
            for position in self.positions[:]:
                current_price = await self.get_current_price(position.symbol)
                
                if not current_price:
                    continue
                    
                # Verificar stop loss
                if self.check_stop_loss(position, current_price):
                    await self.close_position(position, current_price, 'stop_loss')
                    continue
                    
                # Verificar target
                if self.check_target(position, current_price):
                    await self.close_position(position, current_price, 'target')
                    continue
                    
                # Verificar tempo máximo de holding
                if self.check_max_holding_time(position):
                    await self.close_position(position, current_price, 'time_limit')
                    continue
                    
                # Verificar condições de mercado mudadas
                if await self.check_market_conditions_changed(position):
                    await self.close_position(position, current_price, 'conditions_changed')
                    
        except Exception as e:
            logger.error(f"Erro ao monitorar posições: {e}")
            
    async def close_position(self, position: SwingPosition, exit_price: float, reason: str):
        """Fecha uma posição"""
        try:
            # Calcular P&L
            pnl = self.calculate_pnl(position, exit_price)
            roi = (exit_price - position.entry_price) / position.entry_price
            
            if position.side == 'short':
                pnl = -pnl
                roi = -roi
                
            holding_time = (datetime.now() - position.entry_time).days
            
            logger.info(f" POSIÇÃO FECHADA: {position.symbol}")
            logger.info(f"    P&L: ${pnl:.4f} ({roi*100:.2f}%)")
            logger.info(f"   ⏱️ Holding: {holding_time} dias")
            logger.info(f"    Motivo: {reason}")
            
            # Mover para posições fechadas
            self.positions.remove(position)
            self.closed_positions.append(position)
            
            # Salvar no banco de dados
            self.save_closed_position(position, exit_price, pnl, roi, reason)
            
        except Exception as e:
            logger.error(f"Erro ao fechar posição: {e}")
            
    def save_closed_position(self, position: SwingPosition, exit_price: float, 
                           pnl: float, roi: float, reason: str):
        """Salva posição fechada no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO swing_positions 
                (symbol, side, entry_price, entry_time, exit_price, exit_time, 
                 size, pnl, roi, holding_days, setup_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position.symbol, position.side, position.entry_price, position.entry_time,
                exit_price, datetime.now(), position.size, pnl, roi,
                (datetime.now() - position.entry_time).days,
                position.setup_type, position.confidence
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao salvar posição: {e}")
            
    async def swing_trading_loop(self):
        """Loop principal de swing trading"""
        logger.info(" SWING TRADER CONSERVADOR INICIADO")
        logger.info(f"    Capital Mínimo: ${self.capital_minimo}")
        logger.info(f"    Max Posições: {self.max_positions}")
        logger.info(f"    Target: {self.target_roi*100:.1f}%")
        logger.info(f"   ️ Stop Loss: {self.stop_loss*100:.1f}%")
        logger.info(f"   ⏰ Holding Max: 7 dias")
        
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_count += 1
                logger.info(f"\n Ciclo Swing #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 1. Verificar capital
                capital = await self.get_available_capital()
                if capital < self.capital_minimo:
                    logger.warning(f" Capital insuficiente: ${capital:.2f}")
                    await asyncio.sleep(3600)  # Esperar 1 hora
                    continue
                    
                logger.info(f" Capital disponível: ${capital:.2f}")
                
                # 2. Monitorar posições existentes
                await self.monitor_positions()
                
                # 3. Buscar novas oportunidades se houver espaço
                if len(self.positions) < self.max_positions:
                    opportunities = await self.scan_swing_opportunities()
                    
                    if opportunities:
                        # Pegar melhor oportunidade
                        best_opp = opportunities[0]
                        
                        logger.info(f" Melhor oportunidade: {best_opp['symbol']} (Score: {best_opp['score']:.2f})")
                        
                        # Executar trade
                        success = await self.execute_swing_trade(best_opp)
                        
                        if success:
                            logger.info(" Trade swing executado com sucesso!")
                        else:
                            logger.warning(" Trade swing rejeitado por risco")
                    else:
                        logger.info(" Nenhuma oportunidade swing de alta qualidade encontrada")
                else:
                    logger.info(f" Máximo de posições atingido: {len(self.positions)}/{self.max_positions}")
                
                # 4. Esperar próximo ciclo (30 minutos para swing)
                logger.info(f"⏰ Próximo ciclo em 30 minutos...")
                await asyncio.sleep(1800)  # 30 minutos
                
            except KeyboardInterrupt:
                logger.info(" Swing trader interrompido pelo usuário")
                break
                
            except Exception as e:
                logger.error(f" Erro no loop principal: {e}")
                await asyncio.sleep(300)  # Esperar 5 minutos em caso de erro
                
        logger.info(" Swing trader finalizado")
        
    def get_performance_summary(self) -> Dict:
        """Obtém resumo de performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*), SUM(pnl), AVG(roi), AVG(holding_days)
                FROM swing_positions 
                WHERE exit_time IS NOT NULL
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            total_trades = result[0] or 0
            total_pnl = result[1] or 0
            avg_roi = result[2] or 0
            avg_holding = result[3] or 0
            
            return {
                'total_trades': total_trades,
                'total_pnl': total_pnl,
                'avg_roi': avg_roi,
                'avg_holding_days': avg_holding,
                'win_rate': self.calculate_win_rate(),
                'current_positions': len(self.positions)
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter performance: {e}")
            return {}
            
    def calculate_win_rate(self) -> float:
        """Calcula taxa de acerto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(CASE WHEN pnl > 0 THEN 1 END), COUNT(*)
                FROM swing_positions 
                WHERE exit_time IS NOT NULL
            ''')
            
            wins, total = cursor.fetchone()
            conn.close()
            
            return (wins / total * 100) if total > 0 else 0.0
            
        except Exception:
            return 0.0

# Funções auxiliares (simplificadas para exemplo)
    async def get_current_price(self, symbol: str) -> float:
        """Obtém preço atual"""
        return 50.0  # Simulado
        
    async def get_multi_timeframe_data(self, symbol: str) -> Dict:
        """Obtém dados de múltiplos timeframes"""
        return {
            '1h': {'close': [50, 51, 49, 52]},
            '4h': {'close': [50, 52, 48, 53]},
            '1d': {'close': [50, 53, 47, 55]}
        }
        
    async def analyze_market_sentiment(self, symbol: str) -> float:
        """Analisa sentimento do mercado"""
        return 0.8  # Simulado
        
    def analyze_liquidity_conditions(self, data: Dict) -> float:
        """Analisa condições de liquidez"""
        return 0.9  # Simulado
        
    def analyze_trend_direction(self, data: Dict) -> str:
        """Analisa direção da tendência"""
        return 'bullish'  # Simulado
        
    def analyze_momentum(self, data: Dict) -> str:
        """Analisa momentum"""
        return 'oversold_bullish'  # Simulado
        
    def identify_support_resistance(self, data: Dict) -> List[float]:
        """Identifica níveis de suporte/resistência"""
        return [48.0, 52.0, 55.0]  # Simulado
        
    def detect_reversal_patterns(self, data: Dict) -> List[str]:
        """Detecta padrões de reversão"""
        return ['hammer']  # Simulado
        
    def check_stop_loss(self, position: SwingPosition, current_price: float) -> bool:
        """Verifica se stop loss foi atingido"""
        if position.side == 'long':
            return current_price <= position.stop_loss
        else:
            return current_price >= position.stop_loss
            
    def check_target(self, position: SwingPosition, current_price: float) -> bool:
        """Verifica se target foi atingido"""
        if position.side == 'long':
            return current_price >= position.target_price
        else:
            return current_price <= position.target_price
            
    def check_max_holding_time(self, position: SwingPosition) -> bool:
        """Verifica se tempo máximo de holding foi atingido"""
        holding_days = (datetime.now() - position.entry_time).days
        return holding_days >= position.max_hold_days
        
    async def check_market_conditions_changed(self, position: SwingPosition) -> bool:
        """Verifica se condições de mercado mudaram"""
        return False  # Simulado
        
    def calculate_pnl(self, position: SwingPosition, exit_price: float) -> float:
        """Calcula P&L"""
        if position.side == 'long':
            return (exit_price - position.entry_price) * position.size
        else:
            return (position.entry_price - exit_price) * position.size

async def main():
    """Função principal"""
    trader = ConservativeSwingTrader()
    
    # Configurar sinal de interrupção
    def signal_handler(signum, frame):
        logger.info(" Encerrando swing trader...")
        trader.is_running = False
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar trading
    trader.is_running = True
    await trader.swing_trading_loop()

if __name__ == "__main__":
    asyncio.run(main())