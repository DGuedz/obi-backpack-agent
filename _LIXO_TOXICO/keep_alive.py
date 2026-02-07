#!/usr/bin/env python3
"""
 Keep Alive - Anti-Sleep Protocol
Impede que o macOS entre em suspensão para manter os bots rodando.
"""

import os
import sys
import time

def stay_awake():
    print("\n CAFFEINATE MODE: ON")
    print("   ️  Bloqueio de Suspensão Ativado.")
    print("   ️  Pode baixar o brilho da tela para zero.")
    print("     NÃO feche a tampa (se for MacBook) a menos que tenha monitor externo ou app Amphetamine.")
    print("   PRESSIONE CTRL+C PARA PARAR.\n")
    
    # O comando 'caffeinate' do macOS é a forma mais segura e nativa.
    # -i: Impede idle sleep do sistema.
    # -s: Impede sleep do sistema quando na tomada.
    # -d: Impede sleep da tela (opcional, melhor não usar para economizar tela/calor).
    
    try:
        # Executa caffeinate e espera ele terminar (nunca termina sozinho)
        os.system("caffeinate -i -s")
    except KeyboardInterrupt:
        print("\n Modo Caffeinate Desativado. O Mac pode dormir agora.")

if __name__ == "__main__":
    stay_awake()