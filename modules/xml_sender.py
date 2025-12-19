import os
import datetime
import requests
import json
import yaml
from utils.logger import log

# === Pfade vorbereiten ===
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "..", "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

TELEGRAM_CONFIG = config["telegram"]
XML_DIR = os.path.join(base_dir, "..", config["paths"]["xml_output_dir"])

SECRET_FILE_1 = os.path.join(base_dir, "..", TELEGRAM_CONFIG["credentials_file"])
SECRET_FILE_2 = os.path.join(base_dir, "..", TELEGRAM_CONFIG.get("credentials_file_anzeige", ""))

def load_telegram_credentials(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["bot_token"], data["chat_id"]

def send_file_to_telegram(bot_token, chat_id, filepath):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(filepath, "rb") as f:
            files = {"document": (os.path.basename(filepath), f)}
            data = {"chat_id": chat_id}
            response = requests.post(url, files=files, data=data)
        if response.status_code == 200:
            log(f"✅ Datei an Telegram gesendet: {filepath}")
        else:
            log(f"❌ Fehler beim Telegram-Versand: {response.text}")
    except Exception as e:
        log(f"❌ Ausnahme beim Telegram-Versand: {e}")

def send_today_xml():
    today = datetime.date.today()
    filename = f"streams_{today.strftime('%Y-%m')}.xml"
    filepath = os.path.join(XML_DIR, filename)

    if not os.path.exists(filepath):
        log(f"⚠️ XML-Datei für heute nicht gefunden: {filename}")
        return

    for secret_file in [SECRET_FILE_1, SECRET_FILE_2]:
        if secret_file and os.path.exists(secret_file):
            try:
                bot_token, chat_id = load_telegram_credentials(secret_file)
                send_file_to_telegram(bot_token, chat_id, filepath)
            except Exception as e:
                log(f"⚠️ Fehler beim Laden der Telegram-Daten ({secret_file}): {e}")

if __name__ == "__main__":
    send_today_xml()
