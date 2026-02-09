import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# We don't have an endpoint to "get claim code" directly if we lost the initial registration response.
# However, the /agents/status endpoint MIGHT return it or related info.
# Let's check status again specifically looking for claim info or if we can regenerate/find it.
# Wait, the colosseum_skill.md says: "Save the apiKey... You'll also receive a claimCode".
# If we lost it, maybe we can't recover it via API?
# But let's check if it's in our .env or local storage.
# Assuming it might be in .env if I saved it before.

def find_claim_code():
    print("🔍 Searching for Claim Code...")
    
    # 1. Check .env
    claim_code = os.getenv("COLOSSEUM_CLAIM_CODE")
    if claim_code:
        print(f"✅ Found in .env: {claim_code}")
        print(f"👉 Link: https://colosseum.com/agent-hackathon/claim/{claim_code}")
        return

    # 2. Check local files (maybe a registration log?)
    # I don't see a registration log file in the file tree.
    
    print("❌ Claim code not found in .env.")
    print("   If you lost the claim code from the initial registration response,")
    print("   you might need to check your initial terminal logs or contact support if possible.")
    print("   However, check if 'verificationCode' is what is needed? No, 'claimCode' is for prizes.")

if __name__ == "__main__":
    find_claim_code()
