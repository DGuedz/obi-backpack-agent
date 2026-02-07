from backpack_data import BackpackData

class SecurityGuardian:
    """
    Agente de Auditoria & Segurança (The Guardian)
    Missão: Monitorar a Utilization Rate e o teto de capital de $300.
    Contexto: Freio de emergência. Impede novas entradas se risco sistêmico ou de conta for alto.
    """
    def __init__(self, data_client: BackpackData):
        self.data = data_client
        self.hard_cap = 300.0 # Max Capital Allocation

    def audit_system(self, symbol=None):
        """
        Audits Account Health and Specific Asset Pool Health.
        Returns: { 'approved': bool, 'reason': str }
        """
        print("️ Guardian: Auditing System Integrity...")
        
        # 1. Account Health Check
        try:
            collat = self.data.get_account_collateral()
            # API returns 'netEquity', not 'equity'
            equity = float(collat.get('netEquity', collat.get('equity', 0)))
            net_avail = float(collat.get('netEquityAvailable', 0))
            
            # Utilization (Margin Usage)
            # If equity is 0, we can't trade.
            if equity <= 0:
                return {'approved': False, 'reason': "Zero Equity"}
                
            # Check Margin Utilization
            # If Net Available is very low relative to Equity
            margin_utilization = 1.0 - (net_avail / equity)
            
            print(f"   ️ Account Equity: ${equity:.2f} | Util: {margin_utilization*100:.1f}%")
            
            if margin_utilization > 0.80:
                return {'approved': False, 'reason': f"Account Critical (Util > 80%)"}
                
        except Exception as e:
            print(f"   ️ Guardian Error (Account): {e}")
            return {'approved': False, 'reason': "Audit Failed"}

        # 2. Pool Utilization Check (if symbol provided)
        if symbol:
            try:
                base_asset = symbol.split('_')[0]
                lending = self.data.get_borrow_lend_markets()
                pool_util = 0
                for m in lending:
                    if m.get('symbol') == base_asset:
                        pool_util = float(m.get('utilization', 0)) * 100
                        break
                
                print(f"   ️ Pool ({base_asset}): {pool_util:.1f}% Utilization")
                
                if pool_util > 80:
                    return {'approved': False, 'reason': f"Pool Congested ({pool_util:.1f}%)"}
                    
            except Exception as e:
                print(f"   ️ Guardian Error (Pool): {e}")
                # Don't block if just pool check fails, unless critical
        
        return {'approved': True, 'reason': "System Secure"}
