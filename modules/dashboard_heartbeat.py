import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_HEARTBEAT_PATH = os.path.join(BASE_DIR, "..", "status", "dashboard_heartbeat.txt")
MAIN_HEARTBEAT_PATH = os.path.join(BASE_DIR, "..", "status", "main_heartbeat.json")
MAIN_FLAG_PATH = os.path.join(BASE_DIR, "..", "runtime_flags", "main_done.flag")

os.makedirs(os.path.dirname(DASHBOARD_HEARTBEAT_PATH), exist_ok=True)

def write_dashboard_heartbeat():
    with open(DASHBOARD_HEARTBEAT_PATH, "w", encoding="utf-8") as f:
        f.write(datetime.now().isoformat())

def read_main_heartbeat(full=False):
    try:
        with open(MAIN_HEARTBEAT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            ts = datetime.fromisoformat(data.get("timestamp"))
            if full:
                return data.get("state", ""), ts, data.get("next_stream")
            else:
                return data.get("state", ""), ts
    except:
        if full:
            return "", None, None
        return "", None

def was_main_shut_down_cleanly():
    return os.path.exists(MAIN_FLAG_PATH)
