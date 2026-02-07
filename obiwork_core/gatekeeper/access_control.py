import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Configuração (Devem vir de .env)
RPC_URL = os.getenv("EVM_RPC_URL")
LICENSE_CONTRACT_ADDRESS = os.getenv("LICENSE_CONTRACT_ADDRESS")

# ABI Mínima para verifyAccess
LICENSE_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "verifyAccess",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class Gatekeeper:
    def __init__(self):
        if not RPC_URL:
            raise ValueError("EVM_RPC_URL not set in .env")
        if not LICENSE_CONTRACT_ADDRESS:
            raise ValueError("LICENSE_CONTRACT_ADDRESS not set in .env")
            
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        contract_address = Web3.to_checksum_address(LICENSE_CONTRACT_ADDRESS)
        self.contract = self.w3.eth.contract(address=contract_address, abi=LICENSE_ABI)

    def verify_license(self, wallet_address: str) -> dict:
        """
        Verifica on-chain se o endereço possui licença ativa.
        Retorna dict com status e tier.
        """
        if not self.w3.is_connected():
            return {"valid": False, "error": "RPC Connection Failed"}
            
        try:
            # Checksum address
            checksum_address = Web3.to_checksum_address(wallet_address)
            
            # Call Smart Contract
            tier = self.contract.functions.verifyAccess(checksum_address).call()
            
            if tier > 0:
                return {
                    "valid": True,
                    "tier": tier,
                    "tier_name": "Clone #05" if tier == 5 else "Clone #02"
                }
            else:
                return {
                    "valid": False,
                    "error": "No License Found (Tier 0)"
                }
                
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Exemplo de uso
if __name__ == "__main__":
    gate = Gatekeeper()
    # Endereço de teste
    test_addr = "0x123..." 
    print(gate.verify_license(test_addr))
