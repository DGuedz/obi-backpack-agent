import time
import os
from check_volume import check_volume

def monitor_loop():
    print(" MISSION 1M MONITOR: STARTED")
    while True:
        os.system('clear')
        check_volume()
        print("\n Refreshing in 60s...")
        time.sleep(60)

if __name__ == "__main__":
    monitor_loop()
