import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from modules.telegram_sender import send_telegram_message


SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CREDENTIALS_PATH = "secrets/credentials.json"
TOKEN_PATH = "secrets/token.json"

def log(msg):
    print(msg)

def test_token():
    if not os.path.exists(TOKEN_PATH):
        log("❌ Kein token.json vorhanden.")
        return False

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if creds and creds.valid:
            log("✅ token.json ist gültig.")
            return True
        elif creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
            log("🔁 token.json wurde erfolgreich erneuert.")
            return True
        else:
            log("⚠️ token.json ist abgelaufen und nicht erneuerbar.")
            return False
    except Exception as e:
        log(f"❌ Fehler beim Laden des Tokens: {e}")
        return False

def authorize_manually():
    log("🌐 Starte manuelle Autorisierung via Browser...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    with open(TOKEN_PATH, "w") as token:
        token.write(creds.to_json())
    log("✅ Neue token.json wurde erfolgreich gespeichert.")

def list_scheduled_streams():
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        if not creds.valid:
            creds.refresh(Request())
        youtube = build("youtube", "v3", credentials=creds)

        broadcasts = youtube.liveBroadcasts().list(
            part="snippet",
            broadcastStatus="upcoming",
            maxResults=25
        ).execute()

        log("📅 Geplante Streams:")
        for b in broadcasts.get("items", []):
            snippet = b["snippet"]
            title = snippet["title"]
            start = snippet["scheduledStartTime"]
            log(f"• {title} – {start}")

    except Exception as e:
        log(f"❌ Fehler beim Abrufen der geplanten Streams: {e}")

def send_telegram_status():
    msg = "#Sakristei TokenTool\n✅ Das Authentifizierungs-Tool wurde manuell ausgeführt.\n"
    if os.path.exists(TOKEN_PATH):
        msg += "📂 token.json ist vorhanden.\n"
    else:
        msg += "❌ Kein token.json gefunden.\n"
    send_telegram_message(msg)
    log("📤 Telegram-Nachricht gesendet.")

if __name__ == "__main__":
    print("🔧 YouTube Token Tool")
    print("1 = token.json prüfen")
    print("2 = manuell neu autorisieren (Browser)")
    print("3 = geplante Streams anzeigen")
    print("4 = Telegram-Status senden")
    print("0 = beenden")

    while True:
        cmd = input("\nBefehl wählen (0–4): ").strip()
        if cmd == "1":
            test_token()
        elif cmd == "2":
            authorize_manually()
        elif cmd == "3":
            list_scheduled_streams()
        elif cmd == "4":
            send_telegram_status()
        elif cmd == "0":
            break
        else:
            print("❓ Ungültige Eingabe.")
