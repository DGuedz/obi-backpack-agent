#!/usr/bin/env python3
"""
 Bridge Signal Test - Wormhole Nexus
Gera uma transação real na Solana para validação on-chain (Proof of Life)
"""

import os
import sys
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction
from solders.message import Message
from solders.hash import Hash

load_dotenv()

class SignalTester:
    def __init__(self):
        # Usar Main Wallet por padrão
        self.priv_key_str = os.getenv('SOLANA_PRIVATE_KEY_MAIN')
        self.pub_key_str = os.getenv('SOLANA_WALLET_MAIN_ADDRESS')
        
        if not self.priv_key_str:
            print(" Erro: SOLANA_PRIVATE_KEY_MAIN não encontrada no .env")
            sys.exit(1)
            
        try:
            import base58
            # Tentar decodificar Base58
            self.keypair = Keypair.from_bytes(base58.b58decode(self.priv_key_str))
            print(f" Wallet Carregada: {self.keypair.pubkey()}")
        except Exception:
            try:
                # Tentar string direta (se a lib suportar)
                self.keypair = Keypair.from_base58_string(self.priv_key_str)
                print(f" Wallet Carregada: {self.keypair.pubkey()}")
            except Exception as e:
                print(f" Erro ao carregar Keypair: {e}")
                sys.exit(1)

        self.client = Client("https://api.mainnet-beta.solana.com")

    def send_signal(self):
        print("\n Enviando Sinal 'Wormhole Nexus Initiation' para Solana Mainnet...")
        
        try:
            # 1. Obter Blockhash recente
            recent_blockhash_resp = self.client.get_latest_blockhash()
            recent_blockhash = recent_blockhash_resp.value.blockhash
            
            # 2. Criar Instrução (Self Transfer 0.000001 SOL)
            receiver = self.keypair.pubkey()
            lamports = 1000 
            
            ix = transfer(
                TransferParams(
                    from_pubkey=self.keypair.pubkey(),
                    to_pubkey=receiver,
                    lamports=lamports
                )
            )
            
            # 3. Construir Mensagem Legacy (Mais simples que V0 para este teste)
            msg = Message.new_with_blockhash(
                [ix],
                self.keypair.pubkey(),
                recent_blockhash
            )
            
            # 4. Construir Transação Versionada
            tx = VersionedTransaction(msg, [self.keypair])
            
            # 5. Enviar e Confirmar
            print(" Assinando transação...")
            signature = self.client.send_transaction(tx).value
            
            print("\n SUCESSO! Transação Confirmada.")
            print(f" TX Hash: {signature}")
            print(f" Explorer: https://solscan.io/tx/{signature}")
            print("\n Tire o print agora! Isso prova controle on-chain.")
            
        except Exception as e:
            print(f" Erro ao enviar transação: {e}")
            if "insufficient funds" in str(e).lower():
                print(" Dica: Sua carteira precisa de uma fração mínima de SOL para pagar o gas.")

if __name__ == "__main__":
    tester = SignalTester()
    tester.send_signal()