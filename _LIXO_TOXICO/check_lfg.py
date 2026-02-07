#!/usr/bin/env python3
"""
 LFG LIQUIDITY CHECKER
Verifica o saldo da carteira LFG (Degen) para avaliar potencial de consolidação.
"""

import os
from backpack_auth import BackpackAuth
from backpack_data import BackpackData
from dotenv import load_dotenv

load_dotenv()

def check_lfg_balance():
    # Carregar credenciais LFG
    api_key = os.getenv('BACKPACK_API_KEY_LFG')
    api_secret = os.getenv('BACKPACK_API_SECRET_LFG')
    
    if not api_key or not api_secret:
        print(" Erro: Credenciais LFG não encontradas no .env")
        return

    print(" Consultando Saldo LFG (Degen Wallet)...")
    try:
        # Tentar autenticação mais simples primeiro
        import requests
        import time
        import base64
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Reimplementar auth básica aqui para debug se a classe falhar
        auth = BackpackAuth(api_key, api_secret)
        
        # Tentar endpoint público primeiro para ver se a chave conecta
        # Mas balances requer assinatura.
        
        # Debug: Verificar se as chaves carregaram
        # print(f"Key: {api_key[:5]}...")
        
        # Usar a classe data mas tratar erro de None
        data = BackpackData(auth)
        balances = data.get_balances()
        
        if not balances:
            print("️ Falha: Balances retornou vazio ou None. Verifique as chaves LFG.")
            return 0
            
        usdc = balances.get('USDC', {'available': 0, 'locked': 0})
        sol = balances.get('SOL', {'available': 0, 'locked': 0})
        
        usdc_total = float(usdc['available']) + float(usdc['locked'])
        sol_total = float(sol['available']) + float(sol['locked'])
        
        print(f"\n Saldo LFG Disponível:")
        print(f"   USDC: ${float(usdc['available']):.2f}")
        print(f"   SOL:  {float(sol['available']):.4f}")
        
        print(f"\n Total Assets LFG:")
        print(f"   USDC Total: ${usdc_total:.2f}")
        print(f"   SOL Total:  {sol_total:.4f}")
        
        return usdc_total
        
    except Exception as e:
        print(f" Erro ao conectar na conta LFG: {e}")
        return 0

if __name__ == "__main__":
    check_lfg_balance()
