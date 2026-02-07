#!/usr/bin/env python3
import os
import sys
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def main():
    print(" INICIANDO SISTEMA DE TRADING AUTOMATIZADO (OBI RADAR)")
    print("=======================================================")
    print("Doutrina: 'Assim que uma ordem fecha, carta branca para a próxima.'")
    print("Proteção: Stop Loss Atômico (1.5%) + Trailing Stop")
    print("Estratégia: Volume Farming & Profit Snowball")
    print("=======================================================")
    
    # Verificar chaves
    api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        print(" ERRO: BACKPACK_API_KEY não encontrada no .env")
        return
        
    print(f" API Key Detectada: {api_key[:6]}...")
    
    # Importar e rodar o Radar
    try:
        sys.path.append(os.path.join(os.getcwd(), 'tools'))
        from obi_compound_radar import ObiCompoundRadar
        
        radar = ObiCompoundRadar()
        radar.run()
        
    except KeyboardInterrupt:
        print("\n Sistema interrompido pelo usuário.")
    except Exception as e:
        print(f"\n Erro fatal no sistema: {e}")

if __name__ == "__main__":
    main()
