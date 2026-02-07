import os

def view_log(lines=20):
    log_file = "decision_log.txt"
    if not os.path.exists(log_file):
        print(" Log file not found.")
        return

    print(f" Last {lines} decisions from {log_file}:")
    print("=" * 60)
    
    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            for line in last_lines:
                print(line.strip())
    except Exception as e:
        print(f"️ Error reading log: {e}")
    print("=" * 60)

if __name__ == "__main__":
    view_log()
