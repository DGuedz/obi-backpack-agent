#!/usr/bin/env python3
"""
 Return to Base - Liquidity Retrieval
Resgata USDC da Wallet e devolve para a Backpack Exchange para trading.
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
from spl.token.instructions import transfer_checked, TransferCheckedParams, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID

load_dotenv()

# USDC Mint Address (Mainnet)
USDC_MINT = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")

class LiquidityRetriever:
    def __init__(self):
        self.priv_key_str = os.getenv('SOLANA_PRIVATE_KEY_MAIN')
        self.deposit_address = os.getenv('BACKPACK_DEPOSIT_ADDRESS')
        
        if not self.priv_key_str:
            print(" Erro: Chave Privada não encontrada.")
            sys.exit(1)
            
        if not self.deposit_address:
            print(" Erro: BACKPACK_DEPOSIT_ADDRESS não configurado no .env")
            print("    Vá na Backpack Exchange -> Deposit -> Solana (USDC) -> Copie o endereço.")
            sys.exit(1)

        try:
            import base58
            self.keypair = Keypair.from_bytes(base58.b58decode(self.priv_key_str))
            self.dest_pubkey = Pubkey.from_string(self.deposit_address)
            self.client = Client("https://api.mainnet-beta.solana.com")
            print(f" Wallet: {self.keypair.pubkey()}")
            print(f" Destino (Exchange): {self.dest_pubkey}")
        except Exception as e:
            print(f" Erro de inicialização: {e}")
            sys.exit(1)

    def execute_return(self):
        print("\n Iniciando Protocolo de Resgate (USDC)...")
        
        try:
            # 1. Encontrar ATA (Associated Token Account) de USDC da Wallet
            source_ata = get_associated_token_address(self.keypair.pubkey(), USDC_MINT)
            
            # 2. Verificar Saldo USDC
            try:
                balance_resp = self.client.get_token_account_balance(source_ata)
                balance = float(balance_resp.value.ui_amount)
                decimals = balance_resp.value.decimals
                amount_lamports = int(balance_resp.value.amount)
                
                print(f"    Saldo USDC Encontrado: ${balance}")
                
                # SWEEP MODE: Deixar apenas $0.10 para manter a conta ativa
                reserve_amount = 0.10
                amount_to_send = balance - reserve_amount
                
                if amount_to_send < 0.1:
                    print(f"   ️ Saldo (${balance}) insuficiente/já zerado. Nada a enviar.")
                    return
                
                # Recalcular lamports para o valor de envio (USDC tem 6 decimais)
                amount_lamports = int(amount_to_send * (10 ** decimals))
                
                print(f"    Enviando ${amount_to_send:.2f} USDC de volta para a base (Mantendo ${reserve_amount})...")
            except:
                print("    Nenhuma conta USDC encontrada nesta carteira.")
                return

            # 3. Encontrar ATA de Destino (Exchange)
            # Assumindo que o endereço de depósito da Backpack JÁ É um ATA ou suporta transferência direta.
            # Para segurança, vamos enviar para o ATA associado ao endereço de depósito.
            dest_ata = get_associated_token_address(self.dest_pubkey, USDC_MINT)
            recent_blockhash = self.client.get_latest_blockhash().value.blockhash
            
            ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=source_ata,
                    mint=USDC_MINT,
                    dest=dest_ata,
                    owner=self.keypair.pubkey(),
                    amount=amount_lamports,
                    decimals=decimals,
                    signers=[]
                )
            )
            
            msg = Message.new_with_blockhash([ix], self.keypair.pubkey(), recent_blockhash)
            tx = VersionedTransaction(msg, [self.keypair])
            
            # 5. Enviar
            signature = self.client.send_transaction(tx).value
            
            print(f"    RESGATE CONCLUÍDO!")
            print(f"    TX: https://solscan.io/tx/{signature}")
            
        except Exception as e:
            print(f" Falha no Resgate: {e}")

if __name__ == "__main__":
    retriever = LiquidityRetriever()
    retriever.execute_return()