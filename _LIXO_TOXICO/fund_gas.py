#!/usr/bin/env python3
"""
 Fund Gas - Operation Refuel
Converte 5 USDC em SOL e saca para a Main Wallet para habilitar On-Chain Ops.
"""

import os
import time
import requests
import json
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_trade import BackpackTrade
from backpack_data import BackpackData

load_dotenv()

class GasFunder:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.trade = BackpackTrade(self.auth)
        self.data = BackpackData(self.auth)
        self.target_wallet = os.getenv('SOLANA_WALLET_MAIN_ADDRESS')
        self.usdc_amount = 5.0
        
        if not self.target_wallet:
            print(" Erro: SOLANA_WALLET_MAIN_ADDRESS não configurada.")
            exit(1)

    def execute_swap(self):
        print(f" Iniciando Swap: {self.usdc_amount} USDC -> SOL...")
        
        try:
            # 1. Obter Preço SOL
            ticker = self.data.get_ticker("SOL_USDC")
            if not ticker:
                print(" Erro ao obter ticker SOL_USDC")
                return 0
                
            price = float(ticker['lastPrice'])
            print(f"   Preço SOL: ${price}")
            
            # Calcular qtd SOL (Market Buy)
            # 5 USD / Preço = Qtd SOL.
            # Arredondar para 2 casas decimais (precisão padrão segura para SOL Spot)
            sol_quantity = round((self.usdc_amount / price) * 0.99, 2)
            
            print(f"   Comprando ~{sol_quantity} SOL...")
            
            order = self.trade.execute_order(
                symbol="SOL_USDC",
                side="Bid",
                order_type="Market",
                quantity=sol_quantity,
                price=0
            )
            
            if order and order.get('id'):
                print(f"    Swap Executado! ID: {order['id']}")
                return sol_quantity
            else:
                print("    Falha no Swap (Ordem rejeitada ou erro).")
                return 0
        except Exception as e:
            print(f" Erro no Swap: {e}")
            return 0

    def execute_withdrawal(self, sol_amount):
        print(f" Iniciando Saque de {sol_amount} SOL para {self.target_wallet[:6]}...")
        
        # Endpoint de Saque
        url = "https://api.backpack.exchange/api/v1/capital/withdrawals"
        payload = {
            "address": self.target_wallet,
            "blockchain": "Solana",
            "quantity": str(sol_amount),
            "symbol": "SOL"
        }
        
        # Instrução correta para assinatura de saque: withdrawalExecute
        headers = self.auth.get_headers(instruction="withdrawalExecute", params=payload)
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print("    Saque Solicitado com Sucesso!")
                print(f"   ID: {response.json().get('id')}")
            else:
                print(f"   ️  Saque Automático recusado pela API (Segurança/2FA): {response.text}")
                print("    AÇÃO: O SOL já foi comprado. Por favor, realize o saque manualmente no app da Backpack.")
                
        except Exception as e:
            print(f"    Erro na requisição de saque: {e}")

    def run(self):
        print(" GAS FUNDER PROTOCOL")
        print("====================")
        
        # 1. Swap
        sol_bought = self.execute_swap()
        
        if sol_bought > 0:
            time.sleep(2) # Esperar settlement
            # 2. Withdraw
            self.execute_withdrawal(sol_bought)

if __name__ == "__main__":
    funder = GasFunder()
    funder.run()