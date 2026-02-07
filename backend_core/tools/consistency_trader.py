#!/usr/bin/env python3
"""
 CONSISTENCY TRADER - Modo Conservador Pós-S4

Foco: Lucro consistente com risco mínimo durante as 4-6 semanas de testes finais.
Estratégia: Trades de alta qualidade com OBI forte (0.25+) e alvos pequenos (0.8%).

️ CARACTERÍSTICAS DE SEGURANÇA:
- Alavancagem máxima: 5x (proteção de capital)
- OBI mínimo: 0.25 (qualidade sobre quantidade)
- Target ROE: 0.8% (lucro pequeno mas consistente)
- Stop automático se capital < $50
- Máximo 2 posições simultâneas
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from strategies.sniper_executor import SniperExecutor
from core.risk_manager import RiskManager
from core.data_client import DataClient
from core.transport import Transport

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consistency_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ConsistencyTrader")

class ConsistencyTrader:
    def __init__(self):
        self.transport = Transport()
        self.data_client = DataClient()
        self.risk_manager = RiskManager(self.transport)
        self.sniper = SniperExecutor(
            self.transport, 
            self.data_client, 
            self.risk_manager,
            stealth_mode=True
        )
        
        # Configurar modo conservador
        self.sniper.set_mode("CONSISTENCY_PROFIT")
        
        # Parâmetros de segurança
        self.MIN_CAPITAL = 50.0  # Parar se capital < $50
        self.MAX_POSITIONS = 2   # Máximo 2 posições simultâneas
        self.TRADE_COOLDOWN = 300  # 5 minutos entre trades (evitar overtrading)
        
        self.last_trade_time = datetime.now() - timedelta(minutes=10)
        
    async def check_capital_safety(self):
        """Verifica se temos capital suficiente para continuar trading"""
        try:
            balance = self.transport.get_balance()
            available = balance.get('available', 0)
            
            if available < self.MIN_CAPITAL:
                logger.warning(f" Capital insuficiente: ${available:.2f} < ${self.MIN_CAPITAL}")
                return False, available
                
            return True, available
            
        except Exception as e:
            logger.error(f" Erro ao verificar capital: {e}")
            return False, 0.0
    
    async def check_position_limit(self):
        """Verifica limite de posições abertas"""
        try:
            positions = self.transport.get_positions()
            open_positions = len([p for p in positions if p.get('side') != 'CLOSED'])
            
            if open_positions >= self.MAX_POSITIONS:
                logger.info(f" Limite de posições atingido: {open_positions}/{self.MAX_POSITIONS}")
                return False, open_positions
                
            return True, open_positions
            
        except Exception as e:
            logger.error(f" Erro ao verificar posições: {e}")
            return False, 999
    
    async def check_trade_cooldown(self):
        """Verifica cooldown entre trades"""
        time_since_last = datetime.now() - self.last_trade_time
        if time_since_last.total_seconds() < self.TRADE_COOLDOWN:
            remaining = self.TRADE_COOLDOWN - time_since_last.total_seconds()
            logger.info(f"⏰ Cooldown ativo: {remaining:.0f}s restantes")
            return False
        return True
    
    async def scan_for_opportunities(self):
        """Busca oportunidades de alta qualidade"""
        try:
            # Scan de mercado focado em qualidade
            logger.info(" Escaneando mercado para oportunidades de alta qualidade...")
            
            # Obter lista de symbols com volume adequado
            symbols = self.data_client.get_top_symbols(min_volume=1000000)  # 1M+ volume
            
            opportunities = []
            for symbol in symbols[:10]:  # Limitar a top 10 para foco
                try:
                    # Análise OBI
                    obi_data = self.data_client.get_obi(symbol)
                    obi_strength = abs(obi_data.get('imbalance', 0))
                    
                    # Verificar se OBI é forte o suficiente (0.25+)
                    if obi_strength >= 0.25:
                        # Verificar tendência técnica
                        technical_ok = await self.sniper.oracle.validate_technical_veto(symbol)
                        
                        if technical_ok:
                            opportunities.append({
                                'symbol': symbol,
                                'obi_strength': obi_strength,
                                'direction': 'LONG' if obi_data.get('imbalance', 0) > 0 else 'SHORT',
                                'confidence': min(obi_strength * 2, 0.9)  # Max 90% confiança
                            })
                            
                            logger.info(f" Oportunidade encontrada: {symbol} | OBI: {obi_strength:.3f} | Dir: {opportunities[-1]['direction']}")
                    
                except Exception as e:
                    logger.debug(f"️ Erro ao analisar {symbol}: {e}")
                    continue
            
            # Ordenar por força OBI
            opportunities.sort(key=lambda x: x['obi_strength'], reverse=True)
            return opportunities[:3]  # Top 3 oportunidades
            
        except Exception as e:
            logger.error(f" Erro no scan de oportunidades: {e}")
            return []
    
    async def execute_trade(self, opportunity):
        """Executa trade com validações de segurança"""
        try:
            symbol = opportunity['symbol']
            direction = opportunity['direction']
            
            logger.info(f" Executando trade: {symbol} {direction} | Confiança: {opportunity['confidence']:.1%}")
            
            # Executar via sniper executor
            success = await self.sniper.execute_atomic_trade(symbol, direction)
            
            if success:
                self.last_trade_time = datetime.now()
                logger.info(f" Trade executado com sucesso: {symbol} {direction}")
                return True
            else:
                logger.warning(f"️ Trade falhou: {symbol} {direction}")
                return False
                
        except Exception as e:
            logger.error(f" Erro ao executar trade: {e}")
            return False
    
    async def monitor_and_close(self):
        """Monitora posições e fecha quando atinge target ou timeout"""
        try:
            positions = self.transport.get_positions()
            
            for position in positions:
                if position.get('side') == 'CLOSED':
                    continue
                
                symbol = position.get('symbol')
                entry_price = float(position.get('entry_price', 0))
                current_price = float(position.get('current_price', 0))
                side = position.get('side', '').upper()
                
                # Calcular ROE atual
                if side == 'LONG':
                    roe = (current_price - entry_price) / entry_price * 100
                else:  # SHORT
                    roe = (entry_price - current_price) / entry_price * 100
                
                # Verificar se atingiu target (0.8%)
                if roe >= 0.8:
                    logger.info(f" Target atingido: {symbol} {side} | ROE: {roe:.2f}%")
                    await self.sniper.close_position(symbol)
                
                # Verificar timeout (30 minutos sem lucro)
                elif datetime.now().timestamp() - position.get('timestamp', 0) > 1800 and roe <= 0:
                    logger.info(f"⏰ Timeout: {symbol} {side} | ROE: {roe:.2f}% | Fechando...")
                    await self.sniper.close_position(symbol)
                    
        except Exception as e:
            logger.error(f" Erro ao monitorar posições: {e}")
    
    async def trading_loop(self):
        """Loop principal de trading conservador"""
        logger.info(" CONSISTENCY TRADER INICIADO - Modo Ultra Conservador")
        logger.info(f"️ Config: Leverage 5x | Target 0.8% | OBI Min 0.25 | Max Pos {self.MAX_POSITIONS}")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n Ciclo #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # 1. Verificar capital
                capital_safe, available = await self.check_capital_safety()
                if not capital_safe:
                    logger.warning(f" Trading pausado. Capital: ${available:.2f}")
                    await asyncio.sleep(300)  # Esperar 5 minutos
                    continue
                
                # 2. Verificar limite de posições
                positions_ok, open_positions = await self.check_position_limit()
                if not positions_ok:
                    logger.info(f" Máximo de posições abertas: {open_positions}")
                    # Apenas monitorar e fechar se necessário
                    await self.monitor_and_close()
                    await asyncio.sleep(60)  # Esperar 1 minuto
                    continue
                
                # 3. Verificar cooldown
                if not await self.check_trade_cooldown():
                    await asyncio.sleep(30)  # Esperar 30 segundos
                    continue
                
                # 4. Monitorar posições existentes
                await self.monitor_and_close()
                
                # 5. Buscar novas oportunidades
                opportunities = await self.scan_for_opportunities()
                
                if opportunities:
                    # Executar melhor oportunidade
                    best_opp = opportunities[0]
                    success = await self.execute_trade(best_opp)
                    
                    if success:
                        logger.info(f" Trade executado. Aguardando próximo ciclo...")
                else:
                    logger.info(" Nenhuma oportunidade de alta qualidade encontrada")
                
                # 6. Esperar próximo ciclo (2 minutos)
                logger.info(f"⏰ Próximo ciclo em 2 minutos...")
                await asyncio.sleep(120)
                
            except KeyboardInterrupt:
                logger.info(" Trading interrompido pelo usuário")
                break
                
            except Exception as e:
                logger.error(f" Erro no loop principal: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto em caso de erro
    
    async def run(self):
        """Executar trader conservador"""
        try:
            await self.trading_loop()
        except Exception as e:
            logger.error(f" Erro fatal: {e}")
            raise

# Entry point
if __name__ == "__main__":
    trader = ConsistencyTrader()
    asyncio.run(trader.run())