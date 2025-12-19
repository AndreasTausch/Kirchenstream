import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
import os
import json
import yaml
from utils.logger import log

# === Konfiguration sicher laden relativ zum Modulpfad ===
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "..", "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
EMAIL_CONFIG = config["email"]

SECRETS_PATH = os.path.join(base_dir, "..", EMAIL_CONFIG["credentials_file"])

def load_mail_credentials():
    with open(SECRETS_PATH, "r", encoding="utf-8") as f:
        secrets = json.load(f)
    return secrets["email"], secrets["app_password"]

def send_stream_overview_email(file_path):
    if not os.path.exists(file_path):
        log(f"❌ Datei nicht gefunden: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    today_str = datetime.today().strftime("%Y-%m-%d")
    subject = f"YouTube-Streams vom {today_str}"
    email_address, app_password = load_mail_credentials()

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_address
    message["To"] = email_address
    message.set_content(f"""Hallo,

hier ist die Übersicht der geplanten YouTube-Streams vom {today_str}:

{file_content}

Viele Grüße,
dein automatischer Livestream-Planer
""")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(email_address, app_password)
            server.send_message(message)
        log(f"✅ E-Mail erfolgreich gesendet an {email_address}")
        return True
    except Exception as e:
        log(f"❌ Fehler beim Senden der E-Mail: {e}")
        return False

if __name__ == "__main__":
    today_str = datetime.today().strftime("%Y-%m-%d")
    file_path = os.path.join("youtube_streams_geplant", f"youtube_streams_geplant_{today_str}.txt")
    send_stream_overview_email(file_path)
