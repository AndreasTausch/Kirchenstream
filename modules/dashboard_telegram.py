import os
import json
import requests
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TELEGRAM_CREDENTIALS_PATH = os.path.join(BASE_DIR, "..", "secrets", "telegram_stgisela.json")

def get_latest_telegram_status():
    try:
        with open(TELEGRAM_CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            creds = json.load(f)

        url = f"https://api.telegram.org/bot{creds['token']}/getUpdates"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            logging.warning(f"Telegram API-Fehler: {r.status_code} – {r.text}")
            return "gray", "📶 St. Gisela (Telegram-Fehler)"

        updates = r.json().get("result", [])[::-1]

        for u in updates:
            msg = u.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id"))
            text = msg.get("text", "").strip().lower()

            logging.debug(f"Telegram-Check: {text} von Chat {chat_id}")

            if chat_id != str(creds["chat_id"]):
                continue  # andere Chats ignorieren

            if "#on" in text:
                return "green", "📶 St. Gisela #On – Stream läuft"
            if "#off" in text:
                return "gray", "📶 St. Gisela #Off – kein Stream"

        return "gray", "📶 St. Gisela – kein gültiger Status gefunden"

    except Exception as e:
        logging.warning(f"Telegram-Verbindungsfehler: {e}")
        return "gray", "📶 St. Gisela – Fehler bei API-Abfrage"
