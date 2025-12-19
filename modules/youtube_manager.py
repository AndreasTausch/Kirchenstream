import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import yaml
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from modules.stream_info import StreamInfo
from modules.telegram_sender import send_telegram_message
from utils.logger import log

# === Basis & Helper ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../modules
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))       # Projektstamm

def _abs(path: str) -> str:
    """Pfad absolut relativ zum Projektstamm auflösen."""
    return path if os.path.isabs(path) else os.path.join(ROOT_DIR, path)

# === Konfiguration laden (absolut) ===
with open(os.path.join(ROOT_DIR, "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CREDENTIALS_PATH = os.path.join(ROOT_DIR, "secrets", "credentials.json")
TOKEN_PATH = os.path.join(ROOT_DIR, "secrets", "token.json")
XML_PATH = os.path.join(ROOT_DIR, "data")  # Verzeichnis für monatliche XML-Dateien

def get_authenticated_service():
    creds = None

    # Token laden
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            log(f"⚠️ Fehler beim Laden des gespeicherten Tokens: {e}")
            creds = None

    # Ungültig oder abgelaufen?
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                log("🔁 Access Token erfolgreich mit refresh_token erneuert.")
                with open(TOKEN_PATH, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            except Exception as e:
                log(f"⚠️ Fehler beim Refresh: {e}")
                if 'invalid_grant' in str(e).lower():
                    log("🧨 Refresh-Token ungültig – token.json wird gelöscht.")
                    try:
                        os.remove(TOKEN_PATH)
                    except Exception as ex:
                        log(f"⚠️ Konnte token.json nicht löschen: {ex}")

                    # Telegram-Hinweis an Sakristei senden
                    try:
                        msg = (
                            "#Sakristei – Fehler bei YouTube Authentifizierung\n"
                            "❌ Das gespeicherte YouTube-Token ist abgelaufen oder ungültig.\n\n"
                            "🛠 Bitte führe manuell das Skript `youtube_token_tool` auf dem Kirchenstream-PC aus,\n"
                            "um die Autorisierung im Browser neu durchzuführen.\n\n"
                            "Dazu in c:\\Kirchestream das Tool mit 📜`python utils/youtube_token_tool.py` starten"
                            "📁 Die Datei `secrets/token.json` wird dabei automatisch neu erzeugt.\n"
                            "Danach läuft alles wieder automatisch."
                        )
                        if config["telegram"].get("notify_errors", True):
                            send_telegram_message(msg)
                    except Exception as tel_e:
                        log(f"⚠️ Fehler beim Senden der Telegram-Nachricht: {tel_e}")

                creds = None

        # Kein gültiges Token → im Autonom-Modus keine Neuanmeldung!
        if not creds or not creds.valid:
            log("❌ Kein gültiger YouTube-Zugang – automatischer Login deaktiviert.")
            return None

    return build("youtube", "v3", credentials=creds)

def to_iso_utc(date_str, time_str):
    local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    year = local.year

    def letzter_sonntag(monat):
        for tag in range(31, 24, -1):
            d = datetime(year, monat, tag)
            if d.weekday() == 6:
                return d

    dst_start = letzter_sonntag(3).replace(hour=2)
    dst_end = letzter_sonntag(10).replace(hour=3)
    offset = timedelta(hours=2 if dst_start <= local < dst_end else 1)
    utc = local - offset
    return utc.isoformat("T") + "Z"

def stream_exists_in_xml(event):
    file_name = f"streams_{event.date[:7]}.xml"
    path = os.path.join(XML_PATH, file_name)
    if not os.path.exists(path):
        return False
    tree = ET.parse(path)
    root = tree.getroot()
    for s in root.findall("stream"):
        if (s.find("date").text == event.date and
            s.find("time").text == event.time and
            s.find("title").text == event.title):
            return True
    return False

def stream_exists_on_youtube(service, event):
    try:
        broadcasts = service.liveBroadcasts().list(
            part="snippet",
            broadcastStatus="upcoming",
            maxResults=50
        ).execute()

        target_start = to_iso_utc(event.date, event.time)[:16]  # Minutenvergleich

        for b in broadcasts.get("items", []):
            snippet = b["snippet"]
            title_match = snippet["title"].strip() == event.title.strip()
            start_match = snippet["scheduledStartTime"].startswith(target_start)
            if title_match and start_match:
                return True
    except Exception as e:
        log(f"⚠️ Fehler bei YouTube-Check: {e}")
    return False

def create_streams(events, output_dir="youtube_streams_geplant"):
    output_dir = _abs(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_filename = os.path.join(output_dir, f"youtube_streams_geplant_{today_str}.txt")

    service = get_authenticated_service()
    if not service:
        msg = "#Sakristei – YouTube übersprungen\n⚠️ YouTube-API derzeit nicht verfügbar – geplante Streams werden nicht angelegt."
        log(msg)
        if config["telegram"].get("notify_errors", True):
            send_telegram_message(msg)
        return []

    all_logs = []
    stream_infos = []
    seen = set()

    for event in events:
        identifier = (event.date, event.time, event.title)
        if identifier in seen:
            msg = f"⚠️ Duplikat innerhalb des Laufs ignoriert: {event.date} {event.time} – {event.title}"
            all_logs.append(msg)
            log(msg)
            continue
        seen.add(identifier)

        if stream_exists_in_xml(event):
            msg = f"⏭️ Lokaler XML-Abgleich: Stream bereits eingetragen – {event.date} {event.time} – {event.title}"
            all_logs.append(msg)
            log(msg)
            continue

        if stream_exists_on_youtube(service, event):
            msg = f"⏭️ YouTube-Abgleich: Stream bereits vorhanden – {event.date} {event.time} – {event.title}"
            all_logs.append(msg)
            log(msg)
            continue

        try:
            iso_time = to_iso_utc(event.date, event.time)
            log(f"🧪 Termin lokal: {event.date} {event.time}")
            log(f"📤 scheduledStartTime an YouTube: {iso_time}")

            broadcast_body = {
                "snippet": {
                    "title": event.title,
                    "description": f"Stream aus {event.location}\n📅 {event.date}  🕒 {event.time}",
                    "scheduledStartTime": iso_time
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": True
                },
                "contentDetails": {
                    "enableAutoStart": True,
                    "enableAutoStop": True
                }
            }
            broadcast_response = service.liveBroadcasts().insert(
                part="snippet,status,contentDetails",
                body=broadcast_body
            ).execute()
            broadcast_id = broadcast_response["id"]
            video_url = f"https://youtube.com/live/{broadcast_id}"

            stream_body = {
                "snippet": {
                    "title": f"RTMP für {event.title}"
                },
                "cdn": {
                    "frameRate": "30fps",
                    "resolution": "1080p",
                    "ingestionType": "rtmp"
                }
            }
            stream_response = service.liveStreams().insert(
                part="snippet,cdn",
                body=stream_body
            ).execute()
            stream_id = stream_response["id"]
            ingestion = stream_response["cdn"]["ingestionInfo"]
            stream_url = ingestion["ingestionAddress"]
            stream_key = ingestion["streamName"]

            service.liveBroadcasts().bind(
                part="id,contentDetails",
                id=broadcast_id,
                streamId=stream_id
            ).execute()

            info = StreamInfo(
                event.date,
                event.time,
                event.title,
                event.location,
                stream_url,
                stream_key,
                video_url
            )
            stream_infos.append(info)
            all_logs.extend(info.to_log_lines())
            log(f"✅ Stream erstellt: {event.title} – {event.date} {event.time}")

        except Exception as e:
            msg = f"❌ Fehler bei Stream-Erstellung: {getattr(event, 'title', 'unbekannt')} – {str(e)}"
            all_logs.append(msg)
            log(msg)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(all_logs))

    return stream_infos
