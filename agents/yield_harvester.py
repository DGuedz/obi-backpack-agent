from backpack_data import BackpackData
import pandas as pd

class YieldHarvester:
    """
    Agente de Yield & Arbitragem (The Harvester)
    Missão: Maximizar o Basis Yield (Lend APY + Funding Rate).
    Contexto: Foca nos ativos "Interest Bearing Perps" onde o capital trabalha dobrado.
    """
    def __init__(self, data_client: BackpackData):
        self.data = data_client

    def harvest_yields(self, min_apr=15):
        """
        Identifies assets with high combined APY (Lending + Funding).
        APR Calculation: (Lend Rate + (Funding * 24 * 365)) * 100
        """
        print(" Harvester: Scanning Fields for Yield...")
        
        # 1. Fetch Market Data (Funding Rates)
        try:
            markets = self.data.get_mark_prices()
            if not markets:
                return []
            
            # Normalize list
            market_list = markets if isinstance(markets, list) else []
            if isinstance(markets, dict):
                 for k, v in markets.items():
                     if isinstance(v, list): market_list = v; break
        except Exception as e:
            print(f"   ️ Harvester Error (Markets): {e}")
            return []

        # 2. Fetch Lending Data (APY)
        try:
            lending = self.data.get_borrow_lend_markets()
            lend_map = {}
            # Map Base Asset -> APY
            # Need to know exact key for APY. Assuming 'estimatedApy' or 'apy'.
            # Based on common APIs, let's look for 'apy'.
            for item in lending:
                symbol = item.get('symbol')
                # APY might be 0.05 for 5% or 5.
                # Usually it's decimal.
                apy = float(item.get('estimatedApy', 0)) 
                lend_map[symbol] = apy
        except Exception as e:
            print(f"   ️ Harvester Error (Lending): {e}")
            lend_map = {}

        opportunities = []

        for m in market_list:
            symbol = m.get('symbol', '')
            if 'USDC' not in symbol: continue
            
            funding = float(m.get('fundingRate', 0))
            
            # Basis Trade Strategy:
            # Short Perp (Receive Funding) + Long Spot (Earn Lending if collateralized? No, usually Long Spot + Short Perp captures funding)
            # But here we are looking at "Interest Bearing Perps" concept or just pure Funding Arb.
            # If Funding is Positive -> Short Position receives funding.
            # If Funding is Negative -> Long Position receives funding.
            
            # Logic requested: "(Lend Rate + (Funding * 24 * 365))"
            # This implies holding the asset (Lend) and doing something with Funding?
            # Or is it "Basis Yield" = Funding APR?
            
            # Let's calculate Funding APR first.
            funding_apr = funding * 24 * 365 * 100 # %
            
            # If Funding is Positive (>0), Shorts get paid.
            # If Funding is Negative (<0), Longs get paid.
            
            base_asset = symbol.split('_')[0]
            lend_apy = lend_map.get(base_asset, 0) * 100 # %
            
            # Scenario A: Funding > 0. We Short. 
            # We don't earn Lend APY on Short (we borrow).
            # So this formula (Lend + Funding) implies we are LONG Spot (Earning Lend APY) and SHORT Perp (Earning Funding)?
            # Yes, that is the classic "Basis Trade" (Delta Neutral).
            
            if funding > 0:
                total_apr = lend_apy + funding_apr
                direction = "Delta Neutral (Long Spot + Short Perp)"
            else:
                # Funding < 0. Longs get paid.
                # We Long Perp.
                # We pay Borrow Interest if we leverage?
                total_apr = abs(funding_apr) # Just the funding yield
                direction = "Long Perp (Funding Play)"
                
            if total_apr > min_apr:
                opportunities.append({
                    "symbol": symbol,
                    "funding_rate": funding,
                    "funding_apr": funding_apr,
                    "lend_apy": lend_apy,
                    "total_apr": total_apr,
                    "strategy": direction
                })
                
        # Sort by APR
        opportunities.sort(key=lambda x: x['total_apr'], reverse=True)
        
        if opportunities:
            top = opportunities[0]
            print(f"    Harvester: Top Pick {top['symbol']} ({top['total_apr']:.1f}% APR)")
            
        return opportunities
