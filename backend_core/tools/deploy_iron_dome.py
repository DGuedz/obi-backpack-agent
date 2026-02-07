import os
import sys
import json
import time
import stat
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(
    filename='logs/security.log',
    level=logging.INFO,
    format='%(asctime)s - IRON_DOME - %(levelname)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

class IronDome:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.honeypot_file = os.path.join(self.root_dir, "_admin_backup_keys.json")
        self.env_file = os.path.join(self.root_dir, ".env")
        
    def secure_env(self):
        """Restricts .env permissions to owner only (600)"""
        logging.info(f" Hardening permissions for {self.env_file}...")
        try:
            if os.path.exists(self.env_file):
                os.chmod(self.env_file, stat.S_IRUSR | stat.S_IWUSR)
                logging.info(" .env secured (0600).")
            else:
                logging.warning("️ .env file not found!")
        except Exception as e:
            logging.error(f" Failed to secure .env: {e}")

    def deploy_honeypot(self):
        """Creates a fake credentials file to lure attackers"""
        logging.info(" Deploying Honeypot Decoy...")
        
        fake_creds = {
            "admin_user": "root_trader",
            "aws_access_key": "AKIA" + "X" * 16, # Fake AWS Key pattern
            "aws_secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "private_key_backup": "-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA..."
        }
        
        try:
            with open(self.honeypot_file, 'w') as f:
                json.dump(fake_creds, f, indent=4)
            
            # Reset permissions to look accessible but tracked
            os.chmod(self.honeypot_file, 0o666) 
            logging.info(f" Honeypot deployed at {self.honeypot_file}")
            
        except Exception as e:
            logging.error(f" Failed to deploy honeypot: {e}")

    def activate_sentinel(self):
        """Creates the sentinel script that watches the honeypot"""
        sentinel_script_path = os.path.join(self.root_dir, "tools", "iron_dome_sentinel.py")
        
        script_content = f"""import os
import time
import logging
import sys
from datetime import datetime

# Configure Sentinel Logging
logging.basicConfig(
    filename='{os.path.join(self.root_dir, "logs/security.log")}',
    level=logging.INFO,
    format='%(asctime)s - SENTINEL - %(levelname)s - %(message)s'
)

HONEYPOT_FILE = "{self.honeypot_file}"

def watch():
    print("️ IRON DOME SENTINEL WATCHING...")
    logging.info("Sentinel started.")
    
    if not os.path.exists(HONEYPOT_FILE):
        logging.error("Honeypot file missing!")
        return

    last_mtime = os.path.getmtime(HONEYPOT_FILE)
    
    while True:
        try:
            current_mtime = os.path.getmtime(HONEYPOT_FILE)
            if current_mtime != last_mtime:
                msg = " INTRUSION ALERT: Honeypot file modified!"
                print(f"\\n{{msg}}")
                logging.critical(msg)
                # Here we could trigger active defense (e.g., kill session, lock files)
                last_mtime = current_mtime
            
            time.sleep(2)
        except FileNotFoundError:
             logging.critical(" INTRUSION ALERT: Honeypot file DELETED!")
             break
        except Exception as e:
            logging.error(f"Sentinel error: {{e}}")
            time.sleep(5)

if __name__ == "__main__":
    watch()
"""
        try:
            with open(sentinel_script_path, 'w') as f:
                f.write(script_content)
            logging.info(f" Sentinel script created at {sentinel_script_path}")
        except Exception as e:
             logging.error(f" Failed to create sentinel script: {e}")

    def execute(self):
        print("\n DEPLOYING IRON DOME DEFENSE SYSTEM")
        print("="*40)
        self.secure_env()
        self.deploy_honeypot()
        self.activate_sentinel()
        print("="*40)
        print(" IRON DOME ACTIVE. SYSTEM SECURED.")

if __name__ == "__main__":
    IronDome().execute()
