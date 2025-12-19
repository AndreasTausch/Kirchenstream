import requests
import json
import os
from utils.logger import log  # Logging-Modul einbinden

def send_file_to_telegram(bot_token, chat_id, file_path, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as file:
        files = {
            "document": (filename, file, "application/xml")
        }
        data = {
            "chat_id": chat_id
        }
        if caption:
            data["caption"] = caption

        response = requests.post(url, data=data, files=files)

    if response.status_code != 200:
        raise Exception(f"Telegram-Dateiübertragung fehlgeschlagen: {response.text}")

    result = response.json()
    log(f"📤 Telegram-Datei übertragen: {filename} (message_id: {result.get('result', {}).get('message_id')})")
    return result
