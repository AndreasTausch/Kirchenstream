import sys
import os

# === Pfad zur Hauptprojektstruktur einfügen (für utils.logger) ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import yaml
from utils.logger import log

# === Konfiguration sicher laden relativ zum Modulpfad ===
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "..", "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
TELEGRAM_CONFIG = config["telegram"]

SECRETS_PATHS = {
    "St_Gisela": os.path.join(base_dir, "..", TELEGRAM_CONFIG["credentials_file"]),
    "Anzeige": os.path.join(base_dir, "..", TELEGRAM_CONFIG.get("credentials_file_anzeige", "secrets/telegram_anzeige.json"))
}

def load_telegram_credentials():
    creds = {}
    for key, path in SECRETS_PATHS.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                creds[key] = (data.get("token"), data.get("chat_id"))
        else:
            log(f"⚠️ Datei nicht gefunden: {path}")
    return creds

def send_telegram_message(text):
    results = []
    credentials = load_telegram_credentials()
    for name, (bot_token, chat_id) in credentials.items():
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                log(f"✅ Nachricht an {name} gesendet.")
                results.append(True)
            else:
                log(f"❌ Fehler bei Versand an {name}: {response.text}")
                results.append(False)
        except Exception as e:
            log(f"❌ Ausnahme bei {name}: {e}")
            results.append(False)
    return all(results)

if __name__ == "__main__":
    send_telegram_message("#Test\nDies ist ein Test der Telegram-Integration an beide Bots.")
