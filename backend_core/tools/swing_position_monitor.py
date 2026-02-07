#!/usr/bin/env python3
"""
Monitor de Posições Swing com Alerts Automáticos
Sistema de monitoramento em tempo real para trades de médio prazo (2-7 dias)
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/swing_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SwingAlert:
    """Classe para representar um alerta de swing"""
    alert_id: str
    position_id: str
    symbol: str
    alert_type: str
    trigger_price: float
    current_price: float
    message: str
    severity: str  # INFO, WARNING, CRITICAL
    created_at: datetime
    triggered_at: Optional[datetime] = None
    action_required: str = "MONITOR"

class SwingPositionMonitor:
    """Monitor de posições swing com sistema de alerts"""
    
    def __init__(self):
        # Configurações de monitoramento
        self.check_interval = 300  # 5 minutos
        self.price_tolerance = 0.001  # 0.1% tolerância
        
        # Níveis de alerta
        self.profit_levels = [0.02, 0.035, 0.05]  # 2%, 3.5%, 5%
        self.loss_levels = [-0.01, -0.015, -0.02]  # -1%, -1.5%, -2%
        self.time_alerts = [24, 72, 120]  # 1 dia, 3 dias, 5 dias
        
        # Configurações de notificação
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT')
        
        self.db_path = 'data/swing_monitor.db'
        self.setup_database()
        
    def setup_database(self):
        """Configura banco de dados para monitoramento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de posições ativas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swing_positions (
                position_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL NOT NULL,
                size REAL NOT NULL,
                take_profit REAL,
                stop_loss REAL,
                entry_time TIMESTAMP NOT NULL,
                target_time TIMESTAMP,
                status TEXT DEFAULT 'ACTIVE',
                pnl_realtime REAL DEFAULT 0,
                roi_realtime REAL DEFAULT 0,
                alerts_triggered INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS swing_alerts (
                alert_id TEXT PRIMARY KEY,
                position_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                trigger_price REAL,
                trigger_condition TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                triggered_at TIMESTAMP,
                action_taken TEXT,
                FOREIGN KEY (position_id) REFERENCES swing_positions (position_id)
            )
        ''')
        
        # Tabela de notificações enviadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                recipient TEXT NOT NULL,
                status TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (alert_id) REFERENCES swing_alerts (alert_id)
            )
        ''')
        
        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON swing_positions(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_status ON swing_positions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_position ON swing_alerts(position_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_triggered ON swing_alerts(triggered_at)')
        
        conn.commit()
        conn.close()
        
    async def add_position(self, position_data: Dict) -> bool:
        """Adiciona nova posição para monitoramento"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calcular target time (7 dias a partir da entrada)
            entry_time = datetime.fromisoformat(position_data['entry_time'])
            target_time = entry_time + timedelta(days=7)
            
            cursor.execute('''
                INSERT OR REPLACE INTO swing_positions 
                (position_id, symbol, side, entry_price, current_price, size, 
                 take_profit, stop_loss, entry_time, target_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_data['position_id'],
                position_data['symbol'],
                position_data['side'],
                position_data['entry_price'],
                position_data['current_price'],
                position_data['size'],
                position_data.get('take_profit'),
                position_data.get('stop_loss'),
                entry_time,
                target_time
            ))
            
            conn.commit()
            conn.close()
            
            # Criar alerts padrão para a posição
            await self.create_default_alerts(position_data['position_id'], position_data['symbol'])
            
            logger.info(f" Posição {position_data['position_id']} adicionada ao monitor")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar posição: {e}")
            return False
    
    async def create_default_alerts(self, position_id: str, symbol: str):
        """Cria alerts padrão para uma posição"""
        alerts = []
        
        # Alerts de profit
        for level in self.profit_levels:
            alert_id = f"{position_id}_PROFIT_{int(level*100)}"
            alerts.append({
                'alert_id': alert_id,
                'position_id': position_id,
                'symbol': symbol,
                'alert_type': 'PROFIT_TAKE',
                'trigger_condition': f'roi >= {level}',
                'message': f" {symbol}: Profit {level*100:.1f}% atingido! Considere reduzir ou fechar.",
                'severity': 'INFO' if level < 0.035 else 'WARNING'
            })
        
        # Alerts de loss
        for level in self.loss_levels:
            alert_id = f"{position_id}_LOSS_{int(abs(level)*100)}"
            alerts.append({
                'alert_id': alert_id,
                'position_id': position_id,
                'symbol': symbol,
                'alert_type': 'STOP_LOSS',
                'trigger_condition': f'roi <= {level}',
                'message': f" {symbol}: Loss {abs(level)*100:.1f}% atingido! Avaliar saída imediata.",
                'severity': 'CRITICAL'
            })
        
        # Alerts de tempo
        for hours in self.time_alerts:
            alert_id = f"{position_id}_TIME_{hours}h"
            alerts.append({
                'alert_id': alert_id,
                'position_id': position_id,
                'symbol': symbol,
                'alert_type': 'TIME_ALERT',
                'trigger_condition': f'holding_hours >= {hours}',
                'message': f"⏰ {symbol}: Holding por {hours}h. Verificar tendência e ajustar stops.",
                'severity': 'INFO' if hours < 72 else 'WARNING'
            })
        
        # Alert de vencimento
        alert_id = f"{position_id}_EXPIRY"
        alerts.append({
            'alert_id': alert_id,
            'position_id': position_id,
            'symbol': symbol,
            'alert_type': 'EXPIRY_WARNING',
            'trigger_condition': 'days_to_target <= 1',
            'message': f"️ {symbol}: Target de 7 dias vencendo em 24h! Decisão obrigatória.",
            'severity': 'CRITICAL'
        })
        
        # Salvar alerts no banco
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT OR IGNORE INTO swing_alerts 
                (alert_id, position_id, symbol, alert_type, trigger_condition, message, severity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert['alert_id'],
                alert['position_id'],
                alert['symbol'],
                alert['alert_type'],
                alert['trigger_condition'],
                alert['message'],
                alert['severity'],
                datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f" {len(alerts)} alerts criados para posição {position_id}")
    
    async def monitor_positions(self):
        """Loop principal de monitoramento"""
        logger.info(" Monitor de Posições Swing iniciado")
        
        while True:
            try:
                # Obter posições ativas
                positions = await self.get_active_positions()
                
                if not positions:
                    logger.info(" Nenhuma posição ativa para monitorar")
                    await asyncio.sleep(self.check_interval)
                    continue
                
                logger.info(f" Monitorando {len(positions)} posições ativas")
                
                for position in positions:
                    await self.check_position_alerts(position)
                    await self.update_position_metrics(position)
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto em caso de erro
    
    async def check_position_alerts(self, position: Dict):
        """Verifica alerts para uma posição específica"""
        try:
            position_id = position['position_id']
            symbol = position['symbol']
            current_price = position['current_price']
            entry_price = position['entry_price']
            side = position['side']
            entry_time = datetime.fromisoformat(position['entry_time'])
            
            # Calcular métricas atuais
            roi = self.calculate_roi(current_price, entry_price, side)
            holding_hours = (datetime.now() - entry_time).total_seconds() / 3600
            days_to_target = max(0, (entry_time + timedelta(days=7) - datetime.now()).days)
            
            # Obter alerts não disparados
            alerts = await self.get_pending_alerts(position_id)
            
            for alert in alerts:
                alert_id = alert['alert_id']
                trigger_condition = alert['trigger_condition']
                
                # Avaliar condição de trigger
                should_trigger = self.evaluate_trigger_condition(
                    trigger_condition, roi, holding_hours, days_to_target
                )
                
                if should_trigger:
                    # Disparar alert
                    await self.trigger_alert(alert_id, current_price)
                    
                    # Enviar notificações
                    await self.send_notifications(alert, position)
                    
        except Exception as e:
            logger.error(f"Erro ao verificar alerts da posição {position_id}: {e}")
    
    def calculate_roi(self, current_price: float, entry_price: float, side: str) -> float:
        """Calcula ROI da posição"""
        if side == 'long':
            return (current_price - entry_price) / entry_price
        else:  # short
            return (entry_price - current_price) / entry_price
    
    def evaluate_trigger_condition(self, condition: str, roi: float, holding_hours: float, days_to_target: int) -> bool:
        """Avalia se uma condição de trigger deve ser ativada"""
        try:
            # Parse simples das condições
            if '>=' in condition:
                param, value = condition.split('>=')
                param = param.strip()
                value = float(value.strip())
                
                if param == 'roi':
                    return roi >= value
                elif param == 'holding_hours':
                    return holding_hours >= value
                elif param == 'days_to_target':
                    return days_to_target <= value
            
            elif '<=' in condition:
                param, value = condition.split('<=')
                param = param.strip()
                value = float(value.strip())
                
                if param == 'roi':
                    return roi <= value
                elif param == 'holding_hours':
                    return holding_hours <= value
                elif param == 'days_to_target':
                    return days_to_target <= value
            
            return False
            
        except Exception:
            return False
    
    async def trigger_alert(self, alert_id: str, current_price: float):
        """Marca alert como disparado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE swing_alerts 
                SET triggered_at = ?, trigger_price = ?
                WHERE alert_id = ?
            ''', (datetime.now(), current_price, alert_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f" Alert {alert_id} disparado a ${current_price}")
            
        except Exception as e:
            logger.error(f"Erro ao disparar alert {alert_id}: {e}")
    
    async def send_notifications(self, alert: Dict, position: Dict):
        """Envia notificações para o alert"""
        try:
            # Telegram
            if self.telegram_bot_token and self.telegram_chat_id:
                await self.send_telegram_notification(alert, position)
            
            # Email
            if self.email_sender and self.email_password:
                await self.send_email_notification(alert, position)
            
            # Log local
            logger.info(f" Notificação enviada: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificações: {e}")
    
    async def send_telegram_notification(self, alert: Dict, position: Dict):
        """Envia notificação via Telegram"""
        try:
            message = f"""
 **SWING ALERT** - {alert['severity']}

 **Posição**: {position['symbol']} ({position['side'].upper()})
 **ROI Atual**: {self.calculate_roi(position['current_price'], position['entry_price'], position['side'])*100:.2f}%
⏰ **Tempo**: {(datetime.now() - datetime.fromisoformat(position['entry_time'])).days} dias

 **Alerta**: {alert['message']}

 **Ação**: {alert.get('action_required', 'MONITOR')}
"""
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f" Notificação Telegram enviada")
            else:
                logger.error(f"Erro Telegram: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
    
    async def send_email_notification(self, alert: Dict, position: Dict):
        """Envia notificação via email"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_recipient
            msg['Subject'] = f"Swing Alert - {position['symbol']} - {alert['severity']}"
            
            body = f"""
Alerta de Swing Trading Detectado

Posição: {position['symbol']} ({position['side']})
Preço Entrada: ${position['entry_price']:.4f}
Preço Atual: ${position['current_price']:.4f}
ROI: {self.calculate_roi(position['current_price'], position['entry_price'], position['side'])*100:.2f}%

Alerta: {alert['message']}
Severidade: {alert['severity']}
Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Ação Recomendada: {alert.get('action_required', 'MONITOR')}
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Enviar email (simplificado - em produção usar SMTP seguro)
            logger.info(f" Email preparado: {alert['message'][:50]}...")
            
        except Exception as e:
            logger.error(f"Erro ao preparar email: {e}")
    
    async def update_position_metrics(self, position: Dict):
        """Atualiza métricas da posição"""
        try:
            position_id = position['position_id']
            
            # Calcular P&L e ROI atualizados
            roi = self.calculate_roi(position['current_price'], position['entry_price'], position['side'])
            pnl = roi * position['size'] * position['entry_price']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE swing_positions 
                SET pnl_realtime = ?, roi_realtime = ?, last_update = ?
                WHERE position_id = ?
            ''', (pnl, roi, datetime.now(), position_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas da posição {position_id}: {e}")
    
    async def get_active_positions(self) -> List[Dict]:
        """Obtém todas as posições ativas"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM swing_positions 
                WHERE status = 'ACTIVE'
                ORDER BY entry_time DESC
            ''')
            
            positions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return positions
            
        except Exception as e:
            logger.error(f"Erro ao obter posições ativas: {e}")
            return []
    
    async def get_pending_alerts(self, position_id: str) -> List[Dict]:
        """Obtém alerts pendentes para uma posição"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM swing_alerts 
                WHERE position_id = ? AND triggered_at IS NULL
                ORDER BY created_at ASC
            ''', (position_id,))
            
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Erro ao obter alerts pendentes: {e}")
            return []
    
    async def get_monitoring_summary(self) -> Dict:
        """Obtém resumo do monitoramento"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Estatísticas gerais
            cursor.execute('SELECT COUNT(*) as total_positions FROM swing_positions WHERE status = "ACTIVE"')
            total_positions = cursor.fetchone()['total_positions']
            
            cursor.execute('SELECT COUNT(*) as total_alerts FROM swing_alerts WHERE triggered_at IS NULL')
            pending_alerts = cursor.fetchone()['total_alerts']
            
            cursor.execute('SELECT COUNT(*) as triggered_alerts FROM swing_alerts WHERE triggered_at IS NOT NULL')
            triggered_alerts = cursor.fetchone()['triggered_alerts']
            
            # Performance
            cursor.execute('SELECT SUM(pnl_realtime) as total_pnl FROM swing_positions WHERE status = "ACTIVE"')
            total_pnl = cursor.fetchone()['total_pnl'] or 0
            
            cursor.execute('SELECT AVG(roi_realtime) as avg_roi FROM swing_positions WHERE status = "ACTIVE"')
            avg_roi = cursor.fetchone()['avg_roi'] or 0
            
            conn.close()
            
            return {
                'total_positions': total_positions,
                'pending_alerts': pending_alerts,
                'triggered_alerts': triggered_alerts,
                'total_pnl': total_pnl,
                'avg_roi': avg_roi,
                'monitoring_active': True,
                'last_update': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo: {e}")
            return {'error': str(e)}

async def main():
    """Função principal de teste"""
    monitor = SwingPositionMonitor()
    
    # Adicionar posição de teste
    test_position = {
        'position_id': 'TEST_SOL_LONG_001',
        'symbol': 'SOL-USDC',
        'side': 'long',
        'entry_price': 50.0,
        'current_price': 52.5,
        'size': 10.0,
        'take_profit': 55.0,
        'stop_loss': 47.5,
        'entry_time': datetime.now().isoformat()
    }
    
    success = await monitor.add_position(test_position)
    if success:
        logger.info(" Posição de teste adicionada")
        
        # Obter resumo
        summary = await monitor.get_monitoring_summary()
        logger.info(f" Resumo do monitoramento: {summary}")
        
        # Testar monitoramento
        await monitor.check_position_alerts(test_position)

if __name__ == "__main__":
    asyncio.run(main())