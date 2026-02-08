import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("COLOSSEUM_API_KEY")
UPDATE_URL = "https://agents.colosseum.com/api/my-project"
METADATA_FILE = os.path.join(os.path.dirname(__file__), "project_metadata.json")

def update_draft():
    if not API_KEY:
        print("❌ COLOSSEUM_API_KEY missing.")
        return

    if not os.path.exists(METADATA_FILE):
        print(f"❌ Metadata file not found: {METADATA_FILE}")
        return

    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)

    print("📤 Updating Project Draft with metadata:")
    print(json.dumps(metadata, indent=2))

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # PUT to update draft
        response = requests.put(UPDATE_URL, headers=headers, json=metadata)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Project Draft Updated!")
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ FAILED: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_draft()
