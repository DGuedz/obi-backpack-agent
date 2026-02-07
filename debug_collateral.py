import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'core'))
sys.path.append(os.path.join(os.getcwd(), '_LEGACY_V1_ARCHIVE'))
from dotenv import load_dotenv
from core.backpack_transport import BackpackTransport

load_dotenv()
transport = BackpackTransport()
collateral = transport.get_account_collateral()
print("RAW COLLATERAL:", json.dumps(collateral, indent=4))
