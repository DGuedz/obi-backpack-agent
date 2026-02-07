
import sys
import os
from dotenv import load_dotenv

# Add Legacy Path
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))

# Load Environment
load_dotenv()

from core.backpack_transport import BackpackTransport
from core.shadow_simulator import ShadowSimulator
from core.gatekeeper import Gatekeeper

def test_shadow():
    print("Testing Shadow Simulator Logic...")
    transport = BackpackTransport()
    gatekeeper = Gatekeeper(transport) # Added Gatekeeper
    shadow = ShadowSimulator(transport)
    
    targets = ["SOL_USDC_PERP", "BTC_USDC_PERP", "ETH_USDC_PERP", "HYPE_USDC_PERP"]
    
    print(f"Targets: {targets}")
    
    approved = shadow.run_simulation_cycle(targets, gatekeeper) # Passed Gatekeeper
    
    print(f"\nApproved Assets: {approved}")

if __name__ == "__main__":
    test_shadow()
