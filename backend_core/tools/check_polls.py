import os
import requests
import json
from dotenv import load_dotenv

def check_active_polls():
    load_dotenv()
    api_key = os.getenv("COLOSSEUM_API_KEY")
    if not api_key:
        print("Missing COLOSSEUM_API_KEY")
        return

    print("Checking for Active Polls...")
    
    url = "https://agents.colosseum.com/api/agents/polls/active"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            poll = res.json()
            print("\nACTIVE POLL FOUND!")
            print(f"Title: {poll.get('title')}")
            print(f"Question: {poll.get('question')}")
            print("Options:")
            for opt in poll.get('options', []):
                print(f"  - [{opt.get('id')}] {opt.get('text')}")
            
            print("\nTo vote, run a curl command with the option ID.")
        elif res.status_code == 404:
            print("No active polls at the moment.")
        else:
            print(f"Error fetching poll: {res.status_code} - {res.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_active_polls()
