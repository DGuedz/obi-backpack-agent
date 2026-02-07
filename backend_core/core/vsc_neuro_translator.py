class VSCNeuroTranslator:
    """
    Tradutor On-Chain -> Estados VSC.
    Transforma dados brutos (float/int) em estados cognitivos (tags VSC).
    Nenhum número bruto deve sair desta classe para o Cérebro.
    """

    @staticmethod
    def translate(market_data):
        """
        Input: Dict com dados de mercado (funding, netflow, oi_delta, rsi, obi).
        Output: Lista de tags VSC (strings).
        """
        states = []
        
        # 1. Funding (Custo do Capital)
        funding = market_data.get('funding', 0.0)
        if funding > 0.0005:
            states.append('funding_rate,high') # Crowded Long
        elif funding < -0.0005:
            states.append('funding_rate,negative') # Crowded Short
        else:
            states.append('funding_rate,neutral')

        # 2. Netflow (Fluxo de Saída/Entrada na Exchange)
        netflow = market_data.get('netflow', 0.0)
        if netflow > 5_000_000: # Entrada massiva de tokens na exchange (Venda provável)
            states.append('exchange_netflow,positive_inflow')
        elif netflow < -5_000_000: # Saída massiva (Acumulação)
            states.append('exchange_netflow,negative_outflow')
        else:
            states.append('exchange_netflow,neutral')

        # 3. Open Interest Delta (Variação de Contratos)
        oi_delta = market_data.get('oi_delta', 0.0) # % change
        if oi_delta > 0.05: # +5%
            states.append('open_interest,expanding_rapidly')
        elif oi_delta < -0.05:
            states.append('open_interest,collapsing')
        else:
            states.append('open_interest,stable')

        # 4. RSI (Momento)
        rsi = market_data.get('rsi', 50.0)
        if rsi > 75:
            states.append('momentum,overbought_extreme')
        elif rsi > 60:
            states.append('momentum,bullish_strong')
        elif rsi < 25:
            states.append('momentum,oversold_extreme')
        elif rsi < 40:
            states.append('momentum,bearish_strong')
        else:
            states.append('momentum,neutral')

        # 5. OBI (Order Book Imbalance)
        obi = market_data.get('obi', 0.0)
        if obi > 0.3:
            states.append('orderbook,buy_wall_dominant')
        elif obi < -0.3:
            states.append('orderbook,sell_wall_dominant')
        else:
            states.append('orderbook,balanced')

        # 6. Smart Money (Whale Activity - Simulado por grandes ordens recentes)
        whale_activity = market_data.get('whale_activity', False)
        if whale_activity:
            states.append('smart_money,active_distribution')

        return states
