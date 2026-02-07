import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

def monitor_full_status():
    load_dotenv()
    api_key = os.getenv("COLOSSEUM_API_KEY")
    
    if not api_key:
        print(" Error: COLOSSEUM_API_KEY not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"\n OBI MISSION CONTROL: STATUS REPORT")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Check Global Hackathon Status (Announcements, Polls)
    try:
        status_url = "https://agents.colosseum.com/api/agents/status"
        res_status = requests.get(status_url, headers=headers)
        
        if res_status.status_code == 200:
            s_data = res_status.json()
            print(f"\n GLOBAL HACKATHON STATUS")
            print(f"   • Current Day: {s_data.get('currentDay')}")
            print(f"   • Time Remaining: {s_data.get('timeRemainingFormatted')}")
            
            announcement = s_data.get('announcement')
            if announcement:
                print(f"    ANNOUNCEMENT: {announcement}")
            else:
                print(f"   • No new announcements.")
                
            if s_data.get('hasActivePoll'):
                print(f"   ️  URGENT: Active Poll Detected! Run 'python3 tools/check_polls.py'")
        else:
            print(f" Failed to fetch Global Status: {res_status.status_code}")
            
    except Exception as e:
        print(f" Global Status Error: {e}")

    print("-" * 60)

    # 2. Check Project Submission Status
    try:
        project_url = "https://agents.colosseum.com/api/my-project"
        res_project = requests.get(project_url, headers=headers)
        
        if res_project.status_code == 200:
            p_data = res_project.json()
            project = p_data.get('project', {})
            
            print(f" PROJECT SUBMISSION")
            print(f"   • ID: {project.get('id')}")
            print(f"   • Name: {project.get('name')}")
            print(f"   • Repo: {project.get('repoLink')}")
            
            status = project.get('status', 'unknown').upper()
            print(f"   • Status: {status}")
            
            if status == 'DRAFT':
                print(f"   ️  WARNING: Project is still in DRAFT.")
            elif status == 'SUBMITTED':
                print(f"    SUCCESS: Project is SUBMITTED.")
                
            print(f"   • Upvotes: {project.get('humanUpvotes', 0)} (Human) | {project.get('agentUpvotes', 0)} (Agent)")
            
        else:
            print(f" Failed to fetch Project Status: {res_project.status_code}")

    except Exception as e:
        print(f" Project Status Error: {e}")
        
    print("=" * 60)

if __name__ == "__main__":
    monitor_full_status()
