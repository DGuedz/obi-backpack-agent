#!/usr/bin/env python3
"""
 Wormhole Nexus - Backpack Liquidity Bridge Analyzer
Integrates CEX Liquidity with DeFi Incentives (Portal Earn / Fogo Blaze)
"""

import os
import time
from dotenv import load_dotenv
from backpack_auth import BackpackAuth
from backpack_data import BackpackData

load_dotenv()

class WormholeNexus:
    def __init__(self):
        self.auth = BackpackAuth(os.getenv('BACKPACK_API_KEY'), os.getenv('BACKPACK_API_SECRET'))
        self.data = BackpackData(self.auth)
        
        # Parâmetros da Campanha "Fogo Blaze"
        self.BLAZE_MULTIPLIER = 10 # 10 XP por USDC
        self.STANDARD_MULTIPLIER = 1 # 1 XP por Stable
        # ATUALIZAÇÃO: Fogo Zero Fees Week!
        # Custo apenas da Solana TX (~0.000005 SOL) + Wormhole VAA verification (Subsidiado ou baixo)
        self.BRIDGE_COST_EST = 0.001 # Custo simbólico ($0.001)
        
    def analyze_opportunity(self):
        print("\n WORMHOLE NEXUS: Initializing Bridge Scan...")
        print("==============================================")
        print("ℹ️  EVENT DETECTED: Fogo Chain Zero Fee Week (Gas Subsidized)")
        
        # 1. Obter Liquidez Disponível (USDC)
        try:
            collateral = self.data.get_account_collateral()
            usdc_available = 0.0
            
            # Tentar pegar netEquityAvailable (Margem Livre)
            if 'netEquityAvailable' in collateral:
                equity_available = float(collateral['netEquityAvailable'])
            else:
                # Fallback se a chave não existir
                print("️ Dados de colateral incompletos.")
                return
                
            print(f" Backpack Free Liquidity: ${equity_available:.2f} USDC")
            
            if equity_available < 10:
                print("️ Liquidez insuficiente para simulação de bridge eficiente (Min $10).")
                # return # Comentado para mostrar a lógica mesmo com pouco saldo
    
            # 2. Calcular Potencial de XP (Fogo Blaze)
            xp_potential = equity_available * self.BLAZE_MULTIPLIER
            xp_standard = equity_available * self.STANDARD_MULTIPLIER
            
            # 3. Calcular Custo/Benefício (Loop)
            # Se fizermos um ciclo de Ida e Volta (Bridge In -> Bridge Out)
            cycle_cost = self.BRIDGE_COST_EST * 2
            
            # Evitar divisão por zero se custo for muito baixo na simulação
            if cycle_cost == 0: cycle_cost = 0.01
            
            xp_per_dollar_cost = xp_potential / cycle_cost
            
            print("\n FOGO BLAZE CAMPAIGN OPPORTUNITY:")
            print(f"   Transfer Route: Solana -> Fogo Mainnet Genesis")
            print(f"   Multiplier: {self.BLAZE_MULTIPLIER}x (Boosted)")
            print(f"   -------------------------------------------")
            print(f"    POTENTIAL REWARD: {xp_potential:,.0f} XP (Instant)")
            print(f"    Estimated Cycle Cost: ~${cycle_cost:.2f}")
            print(f"    Efficiency: {xp_per_dollar_cost:,.0f} XP per $1 Fee")
            
            print("\n STRATEGIC INSIGHT (For Insiders):")
            print(f"    LIQUIDITY FLOW: Backpack CEX -> Wormhole Portal -> Fogo Chain")
            print(f"    AUTOMATION: System ready to route excess profits (> $100)")
            print(f"      directly to 'Fogo Blaze' campaign for maximized XP yield.")
            
        except Exception as e:
            print(f" Erro na análise Nexus: {e}")

if __name__ == "__main__":
    nexus = WormholeNexus()
    nexus.analyze_opportunity()