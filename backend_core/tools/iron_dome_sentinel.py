import os
import time
import logging
import sys
from datetime import datetime

# Configure Sentinel Logging
logging.basicConfig(
    filename='/Users/doublegreen/backpacktrading/logs/security.log',
    level=logging.INFO,
    format='%(asctime)s - SENTINEL - %(levelname)s - %(message)s'
)

HONEYPOT_FILE = "/Users/doublegreen/backpacktrading/_admin_backup_keys.json"

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
                print(f"\n{msg}")
                logging.critical(msg)
                # Here we could trigger active defense (e.g., kill session, lock files)
                last_mtime = current_mtime
            
            time.sleep(2)
        except FileNotFoundError:
             logging.critical(" INTRUSION ALERT: Honeypot file DELETED!")
             break
        except Exception as e:
            logging.error(f"Sentinel error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch()
