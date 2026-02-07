#!/usr/bin/env python3
"""
 CMC DEX SCANNER (v4) - ON-CHAIN INTELLIGENCE
Módulo especializado para consumir a nova suite DEX API da CoinMarketCap.
Objetivo: Trazer dados de liquidez, preço e histórico diretamente da Blockchain (Raydium/Orca)
para validar as oportunidades na Backpack (CEX).
"""

import os
import requests
import json
from dotenv import load_dotenv
from feedback_department import FeedbackDepartment

load_dotenv()

class CMCDexScanner:
    def __init__(self):
        self.api_key = os.getenv('CMC_API_KEY')
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.feedback = FeedbackDepartment()
        
        # Selecionar ambiente (Sandbox ou Pro)
        env = os.getenv('CMC_API_ENV', 'production')
        if env == 'sandbox':
            self.base_url = "https://sandbox-api.coinmarketcap.com"
            # Chave pública de sandbox se a do .env não for válida
            if not self.api_key or len(self.api_key) < 10:
                self.api_key = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c"
        
    def get_headers(self):
        return {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

    def get_dex_pair_latest(self, network_slug="solana", token_address=None):
        """
        Endpoint: /v4/dex/pairs/trade/latest
        Retorna o último trade e preço de um par DEX.
        Útil para saber o preço "Real" on-chain antes da CEX.
        """
        endpoint = "/v4/dex/pairs/trade/latest"
        url = f"{self.base_url}{endpoint}"
        
        # Exemplo: BONK na Solana
        # Precisamos do Contract Address.
        # BONK: DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
        
        if not token_address:
            # Default BONK Address
            token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
            
        params = {
            "network_slug": network_slug,
            "token_address": token_address,
            "limit": 1
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = response.text
                self.feedback.report_incident("CoinMarketCap", str(response.status_code), error_msg, "CRITICAL" if response.status_code >= 500 else "WARNING")
                return {"error": error_msg, "status": response.status_code}
        except Exception as e:
            self.feedback.report_incident("CoinMarketCap", "Exception", str(e), "CRITICAL")
            return {"error": str(e)}

    def get_dex_listings(self, limit=10):
        """
        Endpoint: /v4/dex/listings/quotes
        Lista as top DEX pairs por volume.
        """
        endpoint = "/v4/dex/listings/quotes"
        url = f"{self.base_url}{endpoint}"
        
        params = {
            "limit": limit,
            "sort": "volume_24h",
            "sort_dir": "desc"
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            if response.status_code == 200:
                return response.json()
            else:
                self.feedback.report_incident("CoinMarketCap", str(response.status_code), response.text, "WARNING")
                return {"error": response.text, "status": response.status_code}
        except Exception as e:
            self.feedback.report_incident("CoinMarketCap", "Exception", str(e), "CRITICAL")
            return {"error": str(e)}

    def get_trending_tokens(self):
        """
        Busca tokens em tendência on-chain (Volume + Price Action).
        Foca em Solana Ecosystem (nossa chain principal).
        """
        endpoint = "/v1/cryptocurrency/trending/most-visited" # Endpoint disponível no plano Hobbyist
        url = f"{self.base_url}{endpoint}"
        
        params = {
            "limit": 10
        }
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                solana_tokens = [
                    t for t in data 
                    if any(p.get('platform', {}).get('name') == 'Solana' for p in t.get('quotes', [])) 
                    or 'Solana' in t.get('name', '')
                ]
                # Fallback: Retorna todos se não achar especificamente Solana (para análise macro)
                return solana_tokens if solana_tokens else data
            else:
                self.feedback.report_incident("CoinMarketCap", str(response.status_code), response.text, "WARNING")
                return []
        except Exception as e:
            self.feedback.report_incident("CoinMarketCap", "Exception", str(e), "WARNING")
            return []

if __name__ == "__main__":
    scanner = CMCDexScanner()
    print(" Iniciando Scan DEX (CMC v4) & Trending...")
    trending = scanner.get_trending_tokens()
    print(f" Trending Tokens Detectados: {len(trending)}")
    for t in trending:
        print(f"   • {t['name']} ({t['symbol']})")
    
    # Teste 1: Listings (Top DEX Pairs)
    print("\n    Buscando Top DEX Pairs...")
    listings = scanner.get_dex_listings(limit=3)
    if "data" in listings:
        print(f"    Top 1 Pair: {listings['data'][0]['name']} ({listings['data'][0]['platform']['name']})")
    else:
        print(f"    Erro Listings: {listings}")

    # Teste 2: Specific Pair (BONK)
    print("\n    Verificando BONK On-Chain (Trade Latest)...")
    data = scanner.get_dex_pair_latest(token_address="DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263")
    
    if "data" in data:
        print("    Dados DEX Recebidos!")
        print(json.dumps(data['data'], indent=2))
    else:
        print(f"   ️ Erro Pair Latest: {data}")
        print("   (Se for 401/403, aguardando Chave Pro Válida)")
