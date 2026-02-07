#!/usr/bin/env python3
"""
Configuração e Teste do Sistema de Swing Trading
Script para validar e preparar o ambiente antes da execução
"""

import asyncio
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.swing_trader_conservative import ConservativeSwingTrader
from tools.swing_risk_manager import SwingRiskManager  
from tools.swing_position_monitor import SwingPositionMonitor

class SwingSystemSetup:
    """Classe para setup e teste do sistema de swing trading"""
    
    def __init__(self):
        self.setup_status = {}
        self.test_results = {}
        
    def create_required_directories(self):
        """Cria diretórios necessários"""
        directories = [
            'data',
            'logs',
            'backups',
            'reports'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f" Diretório criado/verificado: {directory}")
    
    def setup_environment_file(self):
        """Configura arquivo .env se não existir"""
        env_template = """# Configurações do Sistema de Swing Trading
# Telegram (opcional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Email (opcional)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@email.com

# Configurações de Risco
MAX_PORTFOLIO_RISK=0.03
MAX_SINGLE_POSITION_RISK=0.01
MAX_DAILY_LOSS=0.02
MAX_DRAWDOWN_ALLOWED=0.05
MAX_POSITIONS=3

# Configurações de Trading
MIN_CAPITAL=50.0
TARGET_ROE=0.03
STOP_LOSS=0.015
LEVERAGE=3
OBI_THRESHOLD=0.35

# Configurações de Monitoramento
CHECK_INTERVAL=300  # 5 minutos
PRICE_TOLERANCE=0.001  # 0.1%
"""
        
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                f.write(env_template)
            print(" Arquivo .env criado com template")
        else:
            print(" Arquivo .env já existe")
    
    def test_database_setup(self):
        """Testa configuração dos bancos de dados"""
        try:
            # Testar banco do trader
            trader = ConservativeSwingTrader()
            print(" Trader inicializado com sucesso")
            
            # Testar banco do risk manager
            risk_manager = SwingRiskManager()
            print(" Risk Manager inicializado com sucesso")
            
            # Testar banco do monitor
            monitor = SwingPositionMonitor()
            print(" Position Monitor inicializado com sucesso")
            
            self.setup_status['databases'] = 'OK'
            
        except Exception as e:
            print(f" Erro no setup de bancos: {e}")
            self.setup_status['databases'] = 'FAILED'
    
    def test_position_creation(self):
        """Testa criação de posição de teste"""
        try:
            monitor = SwingPositionMonitor()
            
            # Criar posição de teste
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
            
            success = asyncio.run(monitor.add_position(test_position))
            
            if success:
                print(" Posição de teste criada com sucesso")
                self.test_results['position_creation'] = 'PASSED'
            else:
                print(" Falha na criação da posição de teste")
                self.test_results['position_creation'] = 'FAILED'
                
        except Exception as e:
            print(f" Erro no teste de criação: {e}")
            self.test_results['position_creation'] = 'FAILED'
    
    def test_alert_system(self):
        """Testa sistema de alerts"""
        try:
            monitor = SwingPositionMonitor()
            
            # Testar criação de alerts
            test_position = {
                'position_id': 'TEST_BTC_SHORT_002',
                'symbol': 'BTC-USDC',
                'side': 'short',
                'entry_price': 45000.0,
                'current_price': 44500.0,
                'size': 0.1,
                'take_profit': 43000.0,
                'stop_loss': 46000.0,
                'entry_time': datetime.now().isoformat()
            }
            
            # Adicionar posição
            asyncio.run(monitor.add_position(test_position))
            
            # Verificar se alerts foram criados
            conn = sqlite3.connect(monitor.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM swing_alerts WHERE position_id = ?', 
                         ('TEST_BTC_SHORT_002',))
            alert_count = cursor.fetchone()[0]
            
            conn.close()
            
            if alert_count > 0:
                print(f" {alert_count} alerts criados automaticamente")
                self.test_results['alert_system'] = 'PASSED'
            else:
                print(" Nenhum alert criado")
                self.test_results['alert_system'] = 'FAILED'
                
        except Exception as e:
            print(f" Erro no teste de alerts: {e}")
            self.test_results['alert_system'] = 'FAILED'
    
    def test_risk_validation(self):
        """Testa validação de risco"""
        try:
            risk_manager = SwingRiskManager()
            
            # Testar validação de posição
            test_result = asyncio.run(
                risk_manager.validate_new_position('SOL-USDC', 10.0, 50.0, 'long')
            )
            
            if test_result[0]:
                print(" Validação de risco aprovou posição de teste")
                self.test_results['risk_validation'] = 'PASSED'
            else:
                print(f"️ Validação de risco rejeitou: {test_result[1]}")
                self.test_results['risk_validation'] = 'REJECTED'
                
        except Exception as e:
            print(f" Erro no teste de risco: {e}")
            self.test_results['risk_validation'] = 'FAILED'
    
    def generate_test_report(self):
        """Gera relatório de testes"""
        print("\n" + "="*60)
        print(" RELATÓRIO DE TESTES DO SISTEMA DE SWING TRADING")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == 'PASSED')
        
        print(f"\nTestes Executados: {total_tests}")
        print(f"Testes Aprovados: {passed_tests}")
        print(f"Taxa de Sucesso: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetalhes dos Testes:")
        for test, result in self.test_results.items():
            status_icon = "" if result == 'PASSED' else "" if result == 'FAILED' else "️"
            print(f"{status_icon} {test}: {result}")
        
        # Verificar setup geral
        print("\nStatus do Setup:")
        for component, status in self.setup_status.items():
            status_icon = "" if status == 'OK' else ""
            print(f"{status_icon} {component}: {status}")
        
        # Recomendações
        print("\n RECOMENDAÇÕES:")
        if passed_tests == total_tests:
            print(" Sistema pronto para execução!")
            print(" Execute: python3 tools/swing_system_integrated.py")
        else:
            print("️ Corrija os testes falhados antes da execução")
            print(" Verifique logs em: logs/swing_system.log")
        
        print("\n" + "="*60)
    
    def cleanup_test_data(self):
        """Limpa dados de teste"""
        try:
            # Remover posições de teste
            db_paths = [
                'data/swing_positions.db',
                'data/swing_monitor.db',
                'data/swing_system.db'
            ]
            
            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Remover dados de teste
                    cursor.execute("DELETE FROM swing_positions WHERE position_id LIKE 'TEST_%'")
                    cursor.execute("DELETE FROM swing_alerts WHERE position_id LIKE 'TEST_%'")
                    
                    conn.commit()
                    conn.close()
                    
                    print(f" Dados de teste removidos de {db_path}")
            
        except Exception as e:
            print(f"️ Erro na limpeza: {e}")
    
    def run_full_setup(self):
        """Executa setup completo"""
        print(" INICIANDO SETUP DO SISTEMA DE SWING TRADING")
        print("="*60)
        
        # 1. Criar diretórios
        print("\n1. Criando diretórios necessários...")
        self.create_required_directories()
        
        # 2. Configurar ambiente
        print("\n2. Configurando ambiente...")
        self.setup_environment_file()
        
        # 3. Testar bancos de dados
        print("\n3. Testando bancos de dados...")
        self.test_database_setup()
        
        # 4. Testar componentes
        print("\n4. Testando sistema de posições...")
        self.test_position_creation()
        
        print("\n5. Testando sistema de alerts...")
        self.test_alert_system()
        
        print("\n6. Testando validação de risco...")
        self.test_risk_validation()
        
        # 5. Gerar relatório
        print("\n7. Gerando relatório final...")
        self.generate_test_report()
        
        # 6. Limpar dados de teste
        print("\n8. Limpando dados de teste...")
        self.cleanup_test_data()
        
        print("\n SETUP CONCLUÍDO!")
        print("="*60)

def main():
    """Função principal"""
    setup = SwingSystemSetup()
    setup.run_full_setup()

if __name__ == "__main__":
    main()