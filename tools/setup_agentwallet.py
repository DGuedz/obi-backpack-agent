import os
import requests
import json
import time

def setup_agentwallet():
    print(" AgentWallet Setup for Colosseum Hackathon")
    print("-------------------------------------------")
    print("To comply with Hackathon rules, we must use AgentWallet for on-chain interactions.")
    
    email = input(" Enter your email to receive OTP: ").strip()
    if not email:
        print(" Email required.")
        return

    print(f" Requesting OTP for {email}...")
    try:
        res = requests.post("https://agentwallet.mcpay.tech/api/connect/start", 
                            json={"email": email},
                            headers={"Content-Type": "application/json"})
        
        if res.status_code != 200:
            print(f" Failed to request OTP: {res.text}")
            return
            
        data = res.json()
        username = data.get('username')
        print(f" OTP sent! Username: {username}")
        
        otp = input(" Enter the 6-digit OTP received in email: ").strip()
        
        print(" Verifying OTP...")
        verify_res = requests.post("https://agentwallet.mcpay.tech/api/connect/complete",
                                   json={"username": username, "email": email, "otp": otp},
                                   headers={"Content-Type": "application/json"})
                                   
        if verify_res.status_code != 200:
            print(f" Verification failed: {verify_res.text}")
            return
            
        verify_data = verify_res.json()
        api_token = verify_data.get('apiToken')
        evm_address = verify_data.get('evmAddress')
        solana_address = verify_data.get('solanaAddress')
        
        print("\n SUCCESS! AgentWallet Connected.")
        print(f" Username: {username}")
        print(f" Solana Address: {solana_address}")
        print(f" API Token: {api_token[:10]}...")
        
        # Save to ~/.agentwallet/config.json
        config_dir = os.path.expanduser("~/.agentwallet")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "config.json")
        
        config = {
            "username": username,
            "email": email,
            "evmAddress": evm_address,
            "solanaAddress": solana_address,
            "apiToken": api_token
        }
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            
        print(f" Configuration saved to {config_path}")
        print("️  IMPORTANT: Please fund your wallet at https://agentwallet.mcpay.tech/u/" + username)
        
    except Exception as e:
        print(f" Error: {e}")

if __name__ == "__main__":
    setup_agentwallet()
