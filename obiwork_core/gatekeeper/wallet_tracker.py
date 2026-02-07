import json
import os
import argparse
import time
from datetime import datetime
import random

# File to store tracked wallets
TRACKING_FILE = os.path.join(os.path.dirname(__file__), 'tracked_wallets.json')

class WalletTracker:
    def __init__(self):
        self._load_wallets()

    def _load_wallets(self):
        if os.path.exists(TRACKING_FILE):
            try:
                with open(TRACKING_FILE, 'r') as f:
                    self.wallets = json.load(f)
            except:
                self.wallets = []
        else:
            self.wallets = []

    def _save_wallets(self):
        with open(TRACKING_FILE, 'w') as f:
            json.dump(self.wallets, f, indent=2)

    def add_wallet(self, address, label="Ally"):
        # Check if already exists
        for w in self.wallets:
            if w['address'] == address:
                w['label'] = label # Update label
                w['updated_at'] = datetime.now().isoformat()
                self._save_wallets()
                return {"status": "updated", "wallet": w}
        
        new_wallet = {
            "address": address,
            "label": label,
            "added_at": datetime.now().isoformat(),
            "last_active": None
        }
        self.wallets.append(new_wallet)
        self._save_wallets()
        return {"status": "added", "wallet": new_wallet}

    def remove_wallet(self, address):
        initial_len = len(self.wallets)
        self.wallets = [w for w in self.wallets if w['address'] != address]
        if len(self.wallets) < initial_len:
            self._save_wallets()
            return {"status": "removed", "address": address}
        return {"status": "not_found", "address": address}

    def list_wallets(self):
        return self.wallets

    def check_activity(self):
        # Simulate checking activity for tracked wallets
        # In a real scenario, this would call Helius/SolanaFM API
        updates = []
        for w in self.wallets:
            # Simulate random activity
            has_activity = random.random() > 0.7
            if has_activity:
                activity_type = random.choice(["SWAP", "TRANSFER", "MINT", "BURN"])
                amount = round(random.uniform(0.1, 1000), 2)
                token = random.choice(["SOL", "USDC", "RLB", "JUP"])
                
                update = {
                    "address": w['address'],
                    "label": w['label'],
                    "action": f"{activity_type} {amount} {token}",
                    "timestamp": datetime.now().isoformat(),
                    "importance": "HIGH" if amount > 500 else "NORMAL"
                }
                updates.append(update)
                w['last_active'] = datetime.now().isoformat()
        
        self._save_wallets()
        return updates

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OBI Wallet Tracker')
    parser.add_argument('--add', type=str, help='Add wallet address')
    parser.add_argument('--label', type=str, default='Ally', help='Label for the wallet')
    parser.add_argument('--remove', type=str, help='Remove wallet address')
    parser.add_argument('--list', action='store_true', help='List tracked wallets')
    parser.add_argument('--check', action='store_true', help='Check activity for all wallets')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    tracker = WalletTracker()
    
    result = None

    if args.add:
        result = tracker.add_wallet(args.add, args.label)
    elif args.remove:
        result = tracker.remove_wallet(args.remove)
    elif args.list:
        result = tracker.list_wallets()
    elif args.check:
        result = tracker.check_activity()
    
    if result is not None:
        if args.json:
            print(json.dumps(result))
        else:
            print(result)
