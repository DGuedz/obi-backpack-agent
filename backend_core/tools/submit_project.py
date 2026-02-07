import os
import json
import requests
from dotenv import load_dotenv

def submit_project():
    load_dotenv()
    api_key = os.getenv("COLOSSEUM_API_KEY")
    
    if not api_key:
        print(" Error: COLOSSEUM_API_KEY not found in .env")
        return

    metadata_path = "tools/project_metadata.json"
    if not os.path.exists(metadata_path):
        print(f" Error: Metadata file not found at {metadata_path}")
        return

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    print(" Submitting Project to Colosseum Hackathon...")
    print(json.dumps(metadata, indent=2))

    url = "https://agents.colosseum.com/api/my-project"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=metadata, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(" SUCCESS! Project Submitted Successfully.")
            print("Response:", response.json())
        else:
            print("️ Submission Failed.")
            print("Response:", response.text)

    except Exception as e:
        print(f" Exception during submission: {e}")

if __name__ == "__main__":
    submit_project()
