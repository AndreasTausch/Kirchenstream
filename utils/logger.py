import os
from datetime import datetime

log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "logs")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "streamlog.txt")

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(timestamp + message + "\n")