import os
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from utils.logger import log
from modules.telegram_sender import send_telegram_message

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CREDENTIALS_PATH = "secrets/credentials.json"
TOKEN_PATH = "secrets/token.json"

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def delete_old_videos(days_old=10):
    service = get_authenticated_service()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    log(f"🧹 Starte Bereinigung: lösche Videos älter als {days_old} Tage (vor {cutoff.date()})")

    request = service.search().list(
        part="id,snippet",
        forMine=True,
        type="video",
        maxResults=50,
        order="date"
    )
    response = request.execute()

    deleted = []

    for item in response.get("items", []):
        snippet = item["snippet"]
        if snippet.get("liveBroadcastContent") != "none":
            continue  # Nur archivierte Videos (keine geplanten oder laufenden)

        video_id = item["id"]["videoId"]
        published_at = snippet["publishedAt"]
        published_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        if published_date < cutoff:
            try:
                service.videos().delete(id=video_id).execute()
                title = snippet["title"]
                log(f"🗑️ Gelöscht: {title} ({published_date.date()})")
                deleted.append(f"• {title} ({published_date.date()})")
            except Exception as e:
                log(f"⚠️ Fehler beim Löschen von {video_id}: {e}")

    if deleted:
        msg = "#Bereinigung YouTube\n🧹 {} Video(s) gelöscht:\n{}".format(len(deleted), "\n".join(deleted))
    else:
        msg = "#Bereinigung YouTube\n✅ Keine Videos zu löschen."

    send_telegram_message(msg)
    log("📤 Telegram-Zusammenfassung gesendet.")

if __name__ == "__main__":
    delete_old_videos(days_old=10)
