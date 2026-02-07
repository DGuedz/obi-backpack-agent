import requests
import json

def check_solana_balance(address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if "result" in data:
            lamports = data["result"]["value"]
            sol_balance = lamports / 1_000_000_000
            print(f" On-Chain Balance for {address}:")
            print(f"   {sol_balance:.4f} SOL")
        else:
            print(f" Error fetching SOL balance: {data}")

    except Exception as e:
        print(f" Exception: {e}")

def check_token_balance(address, mint_address, token_name):
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            address,
            {"mint": mint_address},
            {"encoding": "jsonParsed"}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        if "result" in data and "value" in data["result"]:
            accounts = data["result"]["value"]
            total_balance = 0
            for acc in accounts:
                info = acc["account"]["data"]["parsed"]["info"]
                balance = float(info["tokenAmount"]["uiAmount"])
                total_balance += balance
            
            print(f"   {total_balance:.2f} {token_name}")
        else:
            print(f"   0.00 {token_name} (No accounts found)")
            
    except Exception as e:
        print(f" Exception checking {token_name}: {e}")

if __name__ == "__main__":
    # Address from .env [MAIN WALLET - Institucional]
    address = "FiMC2XB1vXhKAp6oYLS8vTAj5g4vSC6s8z6Rx8EiQ24Y"
    print(f" Checking Solana On-Chain Balance for {address}...")
    check_solana_balance(address)
    
    # Check USDC
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    check_token_balance(address, USDC_MINT, "USDC")
