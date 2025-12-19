import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import yaml
from obswebsocket import obsws, requests  # obsws-python-Bibliothek

# === Konfiguration laden ===
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "..", "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OBS_CONFIG = config["obs"]

credentials_path = os.path.join(base_dir, "..", OBS_CONFIG["password_file"])
with open(credentials_path, "r", encoding="utf-8") as f:
    password = json.load(f)["password"]

host = OBS_CONFIG["host"]
port = OBS_CONFIG["port"]
print(f"🔌 Verbinde mit OBS WebSocket unter {host}:{port}...")

try:
    ws = obsws(host, port, password)
    ws.connect()
    print("✅ Verbindung erfolgreich hergestellt.")

    # Beispielabfrage: Szenen auflisten
    scenes = ws.call(requests.GetSceneList())
    print("📺 Verfügbare Szenen:")
    for scene in scenes.getScenes():
        print(" -", scene["name"])

    ws.disconnect()
    print("🔌 Verbindung geschlossen.")

except Exception as e:
    print(f"❌ Fehler beim Verbinden mit OBS: {str(e)}")
