import logging

class RiskManager:
    """
    ️ RISK MANAGER
    Guardião do Capital. Implementa as Leis da Constituição.
    1. Lei da Preservação (Risco Max 1%)
    2. Lei da Segregação (70% Operacional / 30% Reserva)
    """
    def __init__(self, transport):
        self.transport = transport
        self.logger = logging.getLogger("RiskManager")
        self.RESERVE_RATIO = 0.05 # [ALL-IN MODE] Reduzido para 5% (Recovery Focus)
        self.MAX_RISK_PER_TRADE = 0.01 # 1% do Capital Disponível

    def check_capital_safety(self):
        """
        Verifica saldo e aplica a Lei da Segregação.
        Retorna (Safe, UsableCapital)
        """
        try:
            collateral = self.transport.get_account_collateral()
            if not collateral:
                return False, 0.0

            # Buscar netEquity (Equity Total) e netEquityAvailable (Disponível)
            total_equity = float(collateral.get('netEquity', collateral.get('equity', 0)))
            available_balance = float(collateral.get('netEquityAvailable', collateral.get('availableToTrade', 0)))

            if total_equity <= 0:
                return False, 0.0

            # Lei da Segregação: 30% é intocável
            reserve_amount = total_equity * self.RESERVE_RATIO
            max_allowed_equity = total_equity - reserve_amount
            
            # O capital usável é o menor entre (Teto Permitido) e (Disponível na API)
            # Ex: Equity 1000. Reserva 300. Teto 700.
            # Se Available for 800 (sem posições), só posso usar 700.
            # Se Available for 500 (posições abertas), posso usar 500.
            
            # Se já estamos usando mais que o permitido (Available < Reserva), STOP.
            # Capital Usado = Total - Available
            used_capital = total_equity - available_balance
            
            if used_capital > max_allowed_equity:
                 # Violação da Reserva
                 return False, 0.0
            
            # Quanto ainda posso usar?
            # Teto Global - Capital Já Usado
            usable_capital = max_allowed_equity - used_capital
            
            # Double check: não posso usar mais do que está available na API
            usable_capital = min(usable_capital, available_balance)

            if usable_capital < 10: # Mínimo operacional
                return False, 0.0

            return True, usable_capital

        except Exception as e:
            self.logger.error(f"Erro no RiskManager: {e}")
            return False, 0.0

    def calculate_position_size(self, symbol, entry_price, sl_price, usable_capital):
        """
        Calcula o tamanho da posição respeitando a Lei da Preservação.
        Risco Máximo = 1% do Capital Usável.
        Risco = |Entry - SL| * Quantity
        Quantity = (Capital * 0.01) / |Entry - SL|
        """
        try:
            risk_amount = usable_capital * self.MAX_RISK_PER_TRADE
            price_diff = abs(entry_price - sl_price)
            
            if price_diff == 0:
                return 0.0
            
            quantity = risk_amount / price_diff
            
            return quantity
        except Exception as e:
            self.logger.error(f"Erro ao calcular size: {e}")
            return 0.0

    def calculate_leveraged_position_size(self, usable_capital, leverage, current_price, depth=None):
        """
        Calcula o tamanho da posição baseado em Alavancagem Fixa (Growth Mode).
        Com Liquidity Sizing: Verifica se a profundidade do mercado suporta a ordem.
        
        Quantity = (Capital * Leverage) / Price
        """
        try:
            notional = usable_capital * leverage
            quantity = notional / current_price
            
            # Liquidity Sizing (Whale Protection)
            if depth:
                # Calcula a liquidez disponível nos top 5 níveis do lado oposto
                # Se quero comprar (Long), preciso ver liquidez de venda (Asks)
                # Se quero vender (Short), preciso ver liquidez de compra (Bids)
                # Por segurança, usamos o MÍNIMO dos dois lados para sizing neutro
                
                bids_vol = sum([float(x[1]) for x in depth.get('bids', [])[:5]]) # Top 5 Bids
                asks_vol = sum([float(x[1]) for x in depth.get('asks', [])[:5]]) # Top 5 Asks
                
                min_liquidity = min(bids_vol, asks_vol)
                
                # Regra: Nossa ordem não pode ser maior que 10% da liquidez imediata (Top 5)
                max_safe_qty = min_liquidity * 0.10
                
                if quantity > max_safe_qty:
                    self.logger.warning(f"️ Liquidity Sizing: Reduzindo quantidade de {quantity:.4f} para {max_safe_qty:.4f} (10% Top5 Depth).")
                    quantity = max_safe_qty
            
            return quantity
        except Exception as e:
            self.logger.error(f"Erro ao calcular size alavancado: {e}")
            return 0.0

    def calculate_dynamic_size(self, usable_capital, base_leverage, current_price, confidence_score, depth=None):
        """
         AGENTIC SIZING (Smart Leverage)
        Ajusta o tamanho da mão baseado na CONFIANÇA do Agente.
        
        Confidence Score (0.0 a 1.0):
        - < 0.3: Setup fraco (Não entra ou 0.5x)
        - 0.3 - 0.5: Normal (1x Leverage Base)
        - 0.5 - 0.7: Forte (1.5x Leverage Base)
        - > 0.7: ALPHA/WHALE (2x a 3x Leverage Base)
        
        Exemplo: Base Lev 9x. Confidence 0.8 (Squeeze + Whale OBI).
        Effective Leverage = 9 * 2 = 18x (Agressividade Institucional)
        """
        try:
            multiplier = 1.0
            
            if confidence_score >= 0.8:
                multiplier = 2.5 # "All-in" mode (Whale Follow)
            elif confidence_score >= 0.6:
                multiplier = 1.5 # Strong Conviction
            elif confidence_score < 0.3:
                multiplier = 0.5 # Weak Conviction
            
            effective_leverage = base_leverage * multiplier
            
            # Trava de Segurança Institucional (Max 20x absoluto)
            effective_leverage = min(effective_leverage, 20.0)
            
            self.logger.info(f" Smart Sizing: Confidence {confidence_score:.2f} -> Multiplier {multiplier}x -> Eff. Lev {effective_leverage:.1f}x")
            
            return self.calculate_leveraged_position_size(usable_capital, effective_leverage, current_price, depth)
            
        except Exception as e:
            self.logger.error(f"Erro no Smart Sizing: {e}")
            return 0.0

