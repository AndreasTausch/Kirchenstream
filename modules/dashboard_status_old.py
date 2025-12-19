import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
import json
import threading
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from modules.dashboard_obs import OBSClient
from modules.dashboard_html import build_html
from modules.dashboard_heartbeat import read_main_heartbeat, was_main_shut_down_cleanly
from modules.dashboard_telegram import get_latest_telegram_status

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOUTUBE_TOKEN_PATH = os.path.join(BASE_DIR, "..", "secrets", "token.json")
XML_DIR = os.path.join(BASE_DIR, "..", "data")

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# === Global State ===
obs_config_path = os.path.join(BASE_DIR, "..", "secrets", "obs_credentials.json")
try:
    with open(obs_config_path, "r") as f:
        obs_cfg = json.load(f)
except:
    obs_cfg = {}

obs_client = OBSClient(
    host="localhost",
    port=obs_cfg.get("port", 4455),
    password=obs_cfg.get("password", "")
)

confirmed_live_ids = set()
error_mode_until = None
live_check_triggered = False
live_check_start = None
active_stream_id = None
lock = threading.Lock()

# === Core Functions ===

def get_youtube_livestatus(broadcast_id):
    try:
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH, SCOPES)
        youtube = build("youtube", "v3", credentials=creds)
        request = youtube.liveBroadcasts().list(part="status", id=broadcast_id)
        response = request.execute()
        if not response["items"]:
            return None
        return response["items"][0]["status"]["lifeCycleStatus"]
    except Exception as e:
        logging.error(f"Fehler beim Abrufen des YouTube-Status: {e}")
        return None

def get_next_stream():
    try:
        now = datetime.now()
        candidates = []
        for offset in range(2):
            month = (now + timedelta(days=offset * 31)).strftime("%Y-%m")
            path = os.path.join(XML_DIR, f"streams_{month}.xml")
            if os.path.exists(path):
                tree = ET.parse(path)
                root = tree.getroot()
                for s in root.findall("stream"):
                    dt = datetime.strptime(s.find("date").text + " " + s.find("time").text, "%Y-%m-%d %H:%M")
                    if dt > now:
                        stream_id = s.find("video_url").text.split("/")[-1]
                        if stream_id not in confirmed_live_ids and stream_id != active_stream_id:
                            candidates.append((dt, s))
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1] if candidates else None
    except Exception as e:
        logging.error(f"Fehler beim Lesen des nächsten Streams: {e}")
        return None

def update_status():
    global confirmed_live_ids, error_mode_until, live_check_triggered, live_check_start, active_stream_id

    # === Initiale Anzeige-Defaults ===
    title, key, video_url, datetime_text = "-", "-", "#", "-"
    status_text = "Kein geplanter Stream"
    status_color = "gray"
    camera_hint = "Automatik Modus"
    camera_hint_color = "red"

    remote_color, remote_text = get_latest_telegram_status()

    try:
        scene = obs_client.get_scene()
        now = datetime.now()
        broadcast_id = None
        stream_element = None  # wird gesetzt auf aktiven oder nächsten Stream

        # === Prüfe auf aktiven Stream (OBS hat bereits gestartet) ===
        if active_stream_id and active_stream_id in confirmed_live_ids:
            broadcast_id = active_stream_id
            status = get_youtube_livestatus(broadcast_id)

            if status == "live":
                stream_element = None  # Details bleiben wie vorher gesetzt
                logging.debug("🔒 Aktiver Stream erkannt – Anzeige bleibt erhalten.")
            else:
                logging.info("🛑 Stream beendet laut YouTube – Status wird freigegeben.")
                with lock:
                    confirmed_live_ids.discard(broadcast_id)
                active_stream_id = None
                broadcast_id = None

        # === Wenn kein aktiver Stream läuft, versuche nächsten geplanten zu holen ===
        if not broadcast_id:
            next_stream = get_next_stream()
            if next_stream is not None:
                broadcast_id_candidate = next_stream.find("video_url").text.strip().split("/")[-1]
                if broadcast_id_candidate:
                    broadcast_id = broadcast_id_candidate
                    stream_element = next_stream
                else:
                    logging.warning("⚠️ Ungültiger YouTube-Link im nächsten Stream – wird ignoriert.")

        # === Wenn gültiger Stream (aktiv oder geplant) bekannt, dann Details übernehmen ===
        if stream_element is not None:
            title = stream_element.find("title").text or "-"
            key = stream_element.find("key").text or "-"
            video_url = stream_element.find("video_url").text or "#"
            sched_dt = datetime.strptime(
                stream_element.find("date").text + " " + stream_element.find("time").text,
                "%Y-%m-%d %H:%M"
            )
            datetime_text = sched_dt.strftime("%Y-%m-%d %H:%M")
            delta = (sched_dt - timedelta(minutes=5) - now).total_seconds()
        else:
            sched_dt = None
            delta = None

        # === Szene prüfen und ggf. aktiven Stream bestätigen ===
        if scene and scene.lower() == "gottesdienst" and broadcast_id:
            status = get_youtube_livestatus(broadcast_id)
            if status == "live":
                with lock:
                    confirmed_live_ids.add(broadcast_id)
                active_stream_id = broadcast_id
                error_mode_until = None
            elif error_mode_until is None:
                error_mode_until = now + timedelta(minutes=120)

        # === Kamera-Modus setzen ===
        if broadcast_id and broadcast_id in confirmed_live_ids:
            if scene and scene.lower() == "gottesdienst":
                camera_hint = "📷 Manuell – bitte Steuerung übernehmen"
                camera_hint_color = "yellow"
            else:
                camera_hint = "Automatik Modus"
                camera_hint_color = "red"
        else:
            camera_hint = "Automatik Modus"
            camera_hint_color = "red"

        # === Fehler-Zeitfenster beenden ===
        if error_mode_until and now > error_mode_until:
            with lock:
                confirmed_live_ids.discard(broadcast_id)
            error_mode_until = None
            live_check_triggered = False

        # === Statusanzeige setzen ===
        if broadcast_id:
            with lock:
                if broadcast_id in confirmed_live_ids:
                    status_text = "✅ Stream läuft"
                    status_color = "green"
                elif delta is not None:
                    if delta > 0:
                        status_text = f"⏳ {int(delta // 60)} Minuten bis Streamstart"
                        status_color = "white"
                    elif -120 <= delta <= 0:
                        status_text = "⏳ Warte auf YouTube..."
                        status_color = "white"
                    elif -2700 <= delta < -120:
                        status_text = "✅ Stream läuft (vermutlich)"
                        status_color = "green"
                    else:
                        status_text = "🔴 Stream beendet – Overlay schließt in 10 Min"
                        status_color = "yellow"

    except Exception as e:
        logging.error("Unbekannter Fehler in update_status()", exc_info=True)

    # === Prüfe Status von main.py ===
    state, ts, next_stream_info = read_main_heartbeat(full=True)
    ts_ok = ts and datetime.now() - ts < timedelta(seconds=90)

    if ts_ok:
        main_status = "läuft"
        main_color = "green"
    elif state == "planned_exit" or was_main_shut_down_cleanly():
        main_status = "planmäßig beendet"
        main_color = "yellow"
    else:
        main_status = "abgestürzt"
        main_color = "red"
    if next_stream_info:
        stream_info_line = f"{next_stream_info.get('date', '?')} {next_stream_info.get('time', '?')} (🔑 {next_stream_info.get('key', '?')})"
        main_status += f"<br>Nächster Stream: {stream_info_line}"



    # === HTML-Datei erzeugen ===
    build_html(
        title, key, video_url, datetime_text, status_text, status_color,
        camera_hint, camera_hint_color, remote_color, remote_text,
        main_color, main_status
    )
