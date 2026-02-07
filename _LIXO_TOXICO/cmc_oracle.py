#!/usr/bin/env python3
"""
 CMC ORACLE - MACRO INTELLIGENCE
Camada de Oráculo que consulta a API CoinMarketCap para obter o sentimento macro do mercado.
Foco: Validar se o mercado está "Risk On" (Bullish) ou "Risk Off" (Bearish/Neutro).
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class CMCOracle:
    def __init__(self):
        self.api_key = os.getenv('CMC_API_KEY')
        
        # Selecionar ambiente correto
        env = os.getenv('CMC_API_ENV', 'production')
        if env == 'sandbox':
            self.base_url = "https://sandbox-api.coinmarketcap.com"
            self.api_key = "b54bcf4d-1bca-4e8e-9a24-22ff2c3d462c" # Chave pública de sandbox
        else:
            self.base_url = "https://pro-api.coinmarketcap.com"
        
        if not self.api_key:
            print("️ CMC_API_KEY não encontrada no .env")
            
    def get_global_metrics(self):
        """
        Retorna métricas globais do mercado cripto.
        Endpoint: /v1/global-metrics/quotes/latest
        Custo: 1 crédito
        """
        url = f"{self.base_url}/v1/global-metrics/quotes/latest"
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get('data', {})
                quote = data.get('quote', {}).get('USD', {})
                
                total_mcap = quote.get('total_market_cap', 0)
                vol_24h = quote.get('total_volume_24h', 0)
                mcap_change = quote.get('total_market_cap_yesterday_percentage_change', 0)
                vol_change = quote.get('total_volume_24h_yesterday_percentage_change', 0)
                
                # Interpretação Macro
                sentiment = "NEUTRAL"
                if mcap_change > 1.5: sentiment = "BULLISH"
                elif mcap_change < -1.5: sentiment = "BEARISH"
                
                return {
                    "total_mcap": total_mcap,
                    "vol_24h": vol_24h,
                    "mcap_change_24h": mcap_change,
                    "vol_change_24h": vol_change,
                    "sentiment": sentiment
                }
            else:
                print(f" Erro CMC API: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f" Erro de conexão CMC: {e}")
            return None

    def get_crypto_greed_index(self):
        """
        Simulação ou busca de índice de medo e ganância (Se disponível na API ou calculado).
        A CMC tem endpoint /v3/fear-and-greed/latest (Verificar doc, pode ser pago ou v3).
        Fallback: Usar variação de volume e mcap como proxy.
        """
        # Para plano Basic, vamos usar proxy de Mcap Change
        metrics = self.get_global_metrics()
        if metrics:
            return metrics['sentiment']
        return "NEUTRAL"

if __name__ == "__main__":
    oracle = CMCOracle()
    print(" Consultando Oráculo CMC...")
    metrics = oracle.get_global_metrics()
    
    if metrics:
        print(f"    Market Cap Change (24h): {metrics['mcap_change_24h']:.2f}%")
        print(f"    Volume Change (24h): {metrics['vol_change_24h']:.2f}%")
        print(f"    Macro Sentiment: {metrics['sentiment']}")
        
        if metrics['sentiment'] == "BULLISH":
            print("    Sinal Verde: Harvester autorizado a operar com mais agressividade.")
        elif metrics['sentiment'] == "BEARISH":
            print("    Sinal Vermelho: Cautela máxima. Reduzir alavancagem.")
        else:
            print("   ️ Sinal Amarelo: Mercado lateral. Foco em Maker/Scalp curto.")
