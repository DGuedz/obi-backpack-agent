import os
import time
import requests
import json
from dotenv import load_dotenv

# Load Env
load_dotenv()

API_KEY = os.getenv("COLOSSEUM_API_KEY")
HEARTBEAT_URL = "https://colosseum.com/heartbeat.md"
STATUS_URL = "https://agents.colosseum.com/api/agents/status"

def fetch_heartbeat():
    try:
        print(f"Fetching Heartbeat from {HEARTBEAT_URL}...")
        response = requests.get(HEARTBEAT_URL)
        if response.status_code == 200:
            print("Heartbeat received. Content preview:")
            print(response.text[:200])
            # Here we could parse the markdown for checklist items
            return True
        else:
            print(f"Failed to fetch heartbeat: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error fetching heartbeat: {e}")
        return False

def check_status():
    if not API_KEY:
        print("COLOSSEUM_API_KEY not found in .env. Skipping status check.")
        return

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Checking Agent Status...")
        response = requests.get(STATUS_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("Status Verified:")
            print(json.dumps(data, indent=2))
            
            # Check for active polls
            if data.get("hasActivePoll"):
                print("ACTIVE POLL DETECTED! Fetching poll details...")
                poll_url = "https://agents.colosseum.com/api/agents/polls/active"
                poll_res = requests.get(poll_url, headers=headers)
                if poll_res.status_code == 200:
                    poll_data = poll_res.json()
                    print("\n--- ACTIVE POLL ---")
                    print(f"ID: {poll_data.get('poll', {}).get('id')}")
                    print(f"Question: {poll_data.get('poll', {}).get('question')}")
                    print("Options:")
                    for opt in poll_data.get('poll', {}).get('options', []):
                        print(f" - [{opt.get('id')}] {opt.get('label')}")
                    print("-------------------\n")
                else:
                    print(f"Failed to fetch poll: {poll_res.status_code}")
        else:
            print(f"Status Check Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error checking status: {e}")

if __name__ == "__main__":
    print("Colosseum Hackathon Heartbeat & Sync")
    fetch_heartbeat()
    check_status()
