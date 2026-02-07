import requests
import time
import json
import os
from datetime import datetime

class ShieldGatekeeper:
    """
    SHIELD PROTOCOL: THE IRON GATE
    Módulo de verificação de conformidade e reputação on-chain.
    
    Princípio: "Proteção Primeiro".
    Verifica se o endereço submetido tem histórico de criação de Tokens fraudulentos (Rugs).
    Powered by VSC Protocol (Value Separated Comparison).
    """
    
    def __init__(self):
        self.rugcheck_api = "https://api.rugcheck.xyz/v1"
        self.spec = self._load_vsc_spec()
        self.risk_threshold = int(self.spec.get('RISK_THRESHOLD', {}).get('VALUE1', 40))
        self.critical_threshold = int(self.spec.get('CRITICAL_RISK', {}).get('VALUE1', 1000))
        
    def _load_vsc_spec(self):
        """Loads SHIELD_PROTOCOL.vsc to configure the gatekeeper."""
        spec_path = os.path.join(os.path.dirname(__file__), 'SHIELD_PROTOCOL.vsc')
        config = {}
        if not os.path.exists(spec_path):
            return config
            
        with open(spec_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('['):
                continue
            parts = line.split('|')
            if len(parts) >= 3:
                key = parts[0]
                config[key] = {
                    'TYPE': parts[1],
                    'VALUE1': parts[2],
                    'VALUE2': parts[3] if len(parts) > 3 else None
                }
        return config

    def _get_created_tokens(self, wallet_address):
        """
        [SIMULATION] Em produção, isso chamaria um Indexer (Helius/SolanaFM)
        para listar todos os tokens onde 'wallet_address' é o 'updateAuthority' ou 'deployer'.
        """
        print(f" Varrendo blockchain por tokens criados por {wallet_address}...")
        # Simulação de tokens encontrados para teste
        # Se a carteira for conhecida como 'bad_actor', retornamos um token ruim simulado
        if wallet_address == "BAD_ACTOR_WALLET_EXAMPLE":
            return ["JUPyiwrYJFskUPiHa7hkeR8VUtkQjDOb2K8L5v8"] # Token Exemplo
        return []

    def check_token_reputation(self, token_mint):
        """
        Consulta a API da RugCheck para ver a saúde do token.
        """
        try:
            url = f"{self.rugcheck_api}/tokens/{token_mint}/report/summary"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                risk_score = data.get('score', 0) # RugCheck Score (quanto maior, pior? Precisa verificar doc)
                # Na RugCheck, score alto geralmente é risco alto.
                # Vamos assumir: Score > 5000 é perigoso (Exemplo).
                # Ajuste conforme a resposta real da API.
                return data
            else:
                print(f"️ Erro ao consultar RugCheck para {token_mint}: {response.status_code}")
                return None
        except Exception as e:
            print(f" Falha de conexão com RugCheck: {e}")
            return None

    def verify_user(self, wallet_address):
        """
        Executa a auditoria completa do usuário.
        Retorna: (Aprovado: bool, Score: int, Motivo: str)
        """
        print(f"\n️ INICIANDO PROTOCOLO SHIELD PARA: {wallet_address}")
        
        # 1. Varredura de Criação
        created_tokens = self._get_created_tokens(wallet_address)
        
        if not created_tokens:
            print(" Nenhum token criado encontrado (Perfil Holder/Trader).")
            # Perfil neutro, mas sem histórico negativo de dev.
            # Score base 80 (Aprovado, mas sujeito a revisão de volume)
            return True, 80, "Clean History (No Deploys)"

        # 2. Auditoria de Tokens Criados
        print(f"️ Encontrados {len(created_tokens)} tokens criados. Auditando...")
        
        for mint in created_tokens:
            report = self.check_token_reputation(mint)
            if report:
                risk = report.get('risks', [])
                score = report.get('score', 0)
                
                print(f"   -> Token {mint}: Score {score}")
                
                # Se tiver riscos críticos (Rug, Mutable Metadata sem Travas, Liquidez Drenada)
                is_danger = any(r['level'] == 'danger' for r in risk if 'level' in r)
                
                if is_danger or score > self.critical_threshold:
                    print(f" ALERTA VERMELHO: Usuário criou token Scam ({mint}).")
                    return False, 0, f"Creator of Scam Token: {mint}"

        print(" Auditoria de tokens concluída. Nenhuma anomalia crítica.")
        return True, 90, "Verified Creator (Clean History)"

import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shield Gatekeeper')
    parser.add_argument('--scan', type=str, help='Wallet address to scan')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    args = parser.parse_args()

    gatekeeper = ShieldGatekeeper()
    
    if args.scan:
        if not args.json:
            print(f"--- Scanning Wallet: {args.scan} ---")
        
        # 1. Get Created Tokens (Simulated for now, or real logic)
        created_tokens = gatekeeper._get_created_tokens(args.scan)
        
        # 2. Audit
        risk_score = 0
        risks = []
        
        if not created_tokens:
            # Clean
            risk_score = 0
        else:
            # Check tokens
            for mint in created_tokens:
                report = gatekeeper.check_token_reputation(mint)
                if report:
                    if report.get('score', 0) > 1000:
                        risk_score += 50
                        risks.append({"name": f"High Risk Token Created: {mint}", "level": "danger"})
        
        result = {
            "address": args.scan,
            "risk_score": risk_score,
            "created_tokens_count": len(created_tokens),
            "risks": risks,
            "status": "APPROVED" if risk_score < 40 else "BLACKLISTED"
        }

        if args.json:
            print(json.dumps(result))
        else:
            print(f"Risk Score: {risk_score}")
            print(f"Status: {result['status']}")
            
    else:
        # Default Test
        # Exemplo (Use um endereço real se quiser testar a API de verdade para um token)
        # Token conhecido (USDC): EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
        
        print("--- Teste de Conexão API RugCheck ---")
        report = gatekeeper.check_token_reputation("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        if report:
            print("API Online! Resposta:")
            print(json.dumps(report, indent=2))
        else:
            print("API Offline ou Token Inválido.")
