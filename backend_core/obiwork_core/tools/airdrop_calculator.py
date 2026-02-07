class OBICalculator:
    def __init__(self):
        # Parâmetros de Mercado (Benchmarks)
        self.GLOBAL_SEASON_VOLUME = 80_000_000_000  # $80 Bilhões (Estimativa Season 4)
        self.MAKER_FEE = 0.0007 # 0.07% (Pior caso Maker)
        
    def calculate_potential(self, capital, leverage, trades_per_day, fdv_billions, alloc_share_pct=20.0):
        # 1. Engenharia de Volume
        volume_per_trade = capital * leverage
        daily_volume = volume_per_trade * trades_per_day * 2 # Open + Close
        season_days = 45 # Dias restantes na Season
        total_volume = daily_volume * season_days
        
        # 2. Custo da Operação (Taxas)
        # O diferencial do OBI WORK é reduzir isso via postOnly=True
        estimated_fees = total_volume * self.MAKER_FEE
        
        # 3. Projeção de Retorno (FDV)
        # Ex: FDV 3Bi, 20% Airdrop = $600M Pool
        airdrop_pool = (fdv_billions * 1e9) * (alloc_share_pct / 100.0)
        user_share = total_volume / self.GLOBAL_SEASON_VOLUME
        estimated_airdrop_value = airdrop_pool * user_share
        
        # 4. ROI (Retorno sobre Investimento em Taxas)
        roi_multiplier = estimated_airdrop_value / estimated_fees if estimated_fees > 0 else 0
        
        return {
            "Total Volume ($)": total_volume,
            "Fees Cost ($)": estimated_fees,
            "Est. Airdrop ($)": estimated_airdrop_value,
            "ROI (x)": roi_multiplier
        }
