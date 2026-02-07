import os
import sys
import hashlib
import time
import logging
from typing import Dict, Any

# Adicionar path raiz para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.vsc_transformer import VSCLayer

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IntegrityAudit")

class IntegrityAudit:
    """
    Módulo de Auditoria Criptográfica OBI (ZK-Lite).
    Gera provas de integridade (Hashes) para cada operação do sistema.
    """
    
    def __init__(self, vault_path: str = "logs/audit_vault.vsc"):
        self.vsc = VSCLayer()
        self.vault_path = vault_path
        
        # Garantir diretório de logs
        os.makedirs(os.path.dirname(self.vault_path), exist_ok=True)

    def _generate_hash(self, data_string: str) -> str:
        """Gera SHA-256 do payload VSC"""
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    def generate_trade_proof(self, trade_payload: Dict[str, Any], oracle_context: Dict[str, Any]) -> str:
        """
        Cria um Certificado de Integridade para um trade executado.
        Combina dados da execução + dados do Oracle no momento da decisão.
        """
        # 1. Extrair dados essenciais em VSC
        timestamp = int(time.time())
        symbol = trade_payload.get('symbol', 'UNK')
        price = trade_payload.get('price', 0)
        qty = trade_payload.get('quantity', 0)
        side = trade_payload.get('side', 'UNK')
        
        obi_score = oracle_context.get('obi_score', 0)
        sentinel_active = oracle_context.get('sentinel_active', False)
        
        # 2. Montar String de Prova (Canonical VSC)
        # PROOF|TS|SYM|SIDE|PRICE|QTY|OBI|SENTINEL
        proof_string = f"PROOF|{timestamp}|{symbol}|{side}|{price}|{qty}|{obi_score}|{1 if sentinel_active else 0}"
        
        # 3. Gerar Hash (Assinatura Digital)
        proof_hash = self._generate_hash(proof_string)
        
        # 4. Registrar no Vault
        self._append_to_vault(proof_hash, proof_string)
        
        return proof_hash

    def _append_to_vault(self, proof_hash: str, proof_string: str):
        """Salva a prova no arquivo de auditoria imutável (append-only)"""
        try:
            with open(self.vault_path, "a") as f:
                # Log Format: HASH|RAW_PROOF
                f.write(f"{proof_hash}|{proof_string}\n")
        except Exception as e:
            logger.error(f"Falha ao escrever no Audit Vault: {e}")

    def verify_proof(self, proof_hash: str) -> bool:
        """
        Verifica se um hash existe no vault e é válido.
        Útil para investidores auditarem trades.
        """
        try:
            if not os.path.exists(self.vault_path):
                return False
                
            with open(self.vault_path, "r") as f:
                for line in f:
                    stored_hash, stored_proof = line.strip().split('|', 1)
                    if stored_hash == proof_hash:
                        # Re-calcular hash para garantir integridade do arquivo
                        recalc_hash = self._generate_hash(stored_proof)
                        return recalc_hash == proof_hash
            return False
        except Exception as e:
            logger.error(f"Erro na verificação de prova: {e}")
            return False

# --- Exemplo de Uso (Simulação) ---
if __name__ == "__main__":
    audit = IntegrityAudit()
    
    # Dados Simulados
    trade_data = {"symbol": "SOL_USDC", "side": "Buy", "price": 145.50, "quantity": 10.0}
    oracle_data = {"obi_score": 0.45, "sentinel_active": True}
    
    print("--- Gerando Prova de Integridade ---")
    proof_hash = audit.generate_trade_proof(trade_data, oracle_data)
    print(f"Trade Hash: {proof_hash}")
    
    print("\n--- Verificando Prova ---")
    is_valid = audit.verify_proof(proof_hash)
    print(f"Integridade Confirmada: {is_valid}")
