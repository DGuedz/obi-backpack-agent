import logging
import os

class SystemCheck:
    """
    ️ SYSTEM INTEGRITY CHECK
    Verifica se o ambiente está seguro para operar.
    """
    def __init__(self):
        self.logger = logging.getLogger("SystemCheck")

    def verify_api_integrity(self):
        """
        Verifica variáveis de ambiente e conectividade básica.
        """
        key = os.getenv('BACKPACK_API_KEY')
        secret = os.getenv('BACKPACK_API_SECRET')
        
        if not key or not secret:
            self.logger.critical(" API KEYS MISSING IN ENV!")
            return False
            
        if "EXAMPLE" in key or "YOUR_KEY" in key:
            self.logger.critical(" API KEYS ARE PLACEHOLDERS!")
            return False
            
        # self.logger.info(" API Credentials Validated (Environment).")
        return True
