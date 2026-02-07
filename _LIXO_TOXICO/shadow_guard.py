#!/usr/bin/env python3
"""
 SHADOW GUARD - EMERGENCY EVACUATION PROTOCOL
Top Secret Level Authorization Required.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.message import Message

load_dotenv()

# --- PROTOCOL SECRETS ---
ACCESS_CODE_HASH = os.getenv("SHADOW_ACCESS_CODE_HASH")
VAULT_ADDRESS = os.getenv('SHADOW_VAULT_ADDRESS')
PRIVATE_KEY = os.getenv('SOLANA_PRIVATE_KEY_MAIN')

class ShadowGuard:
    def __init__(self):
        if not VAULT_ADDRESS:
            print(" ERRO FATAL: 'SHADOW_VAULT_ADDRESS' não definido. Onde guardo o ouro?")
            sys.exit(1)
            
        if not PRIVATE_KEY:
            print(" ERRO: Chave Privada não encontrada.")
            sys.exit(1)
            
        try:
            import base58
            self.keypair = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
            self.vault = Pubkey.from_string(VAULT_ADDRESS)
            self.client = Client("https://api.mainnet-beta.solana.com")
        except Exception as e:
            print(f" Falha na inicialização dos sistemas: {e}")
            sys.exit(1)

    def execute_protocol_omega(self):
        print("\n️  PROTOCOL OMEGA INITIATED ️")
        print("   Evacuating funds to Safe Vault...")
        
        try:
            # 1. Checar Saldo Total
            balance = self.client.get_balance(self.keypair.pubkey()).value
            print(f"    Saldo Detectado: {balance / 10**9:.6f} SOL")
            
            if balance < 10000: # Menos de 0.00001 SOL
                print("    Saldo insuficiente até para o gas.")
                return

            # 2. Calcular Max Transfer (Saldo - Gas)
            # Gas cost approx 5000 lamports per sig
            gas_reserve = 5000 
            amount_to_send = balance - gas_reserve
            
            print(f"    Burning Bridge... Sending {amount_to_send / 10**9:.6f} SOL")
            
            # 3. Construir Transação
            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=self.vault,
                    lamports=amount_to_send
                )
            )
            
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            msg = Message.new_with_blockhash([ix], self.keypair.pubkey(), recent_blockhash)
            tx = VersionedTransaction(msg, [self.keypair])
            
            # 4. Enviar (Skip Preflight para velocidade máxima)
            signature = self.client.send_transaction(tx).value
            
            print("\n EVACUATION COMPLETE.")
            print(f"   ️ Funds Secured in Vault: {VAULT_ADDRESS}")
            print(f"    Proof: https://solscan.io/tx/{signature}")
            
        except Exception as e:
            print(f" FALHA NA EVACUAÇÃO: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shadow Guard Protocol')
    parser.add_argument('--code', type=str, required=True, help='Authorization Code')
    args = parser.parse_args()
    
    if not ACCESS_CODE_HASH:
        print(" ERRO: SHADOW_ACCESS_CODE_HASH não definido.")
        sys.exit(1)

    if args.code != ACCESS_CODE_HASH:
        print(" ACESSO NEGADO. Este incidente será reportado.")
        sys.exit(1)
        
    guard = ShadowGuard()
    guard.execute_protocol_omega()
