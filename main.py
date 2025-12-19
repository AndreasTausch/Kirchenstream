import os
import time
import subprocess
import sys
import psutil
import threading
from datetime import datetime, timedelta
import yaml
import xml.etree.ElementTree as ET
import json
import socket

from modules.web_parser import extract_events
from modules.youtube_manager import create_streams
from modules.mail_sender import send_stream_overview_email
from modules.telegram_sender import send_telegram_message
from modules.obs_controller import OBSController
from modules.xml_writer import append_stream_to_monthly_xml
from modules.stream_info import StreamInfo
from modules.xml_writer import load_todays_streams_from_xml
from modules.telegram_file_sender import send_file_to_telegram
from utils.logger import log
from modules.dashboard_status import get_next_stream 
from modules.obs_controller import next_stream_to_obs
from modules.upload_html_strato import upload_streamlink_html

# === Basisverzeichnisse & Pfad-Helper ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_DIR = os.path.join(BASE_DIR, "status")
RUNTIME_FLAGS_DIR = os.path.join(BASE_DIR, "runtime_flags")
os.makedirs(STATUS_DIR, exist_ok=True)
os.makedirs(RUNTIME_FLAGS_DIR, exist_ok=True)

def _abs(path: str) -> str:
    """Macht einen Pfad absolut relativ zum Skriptordner."""
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)

# === Heartbeat-Pfade (absolut) ===
MAIN_HEARTBEAT = os.path.join(STATUS_DIR, "main_heartbeat.json")
DASHBOARD_HEARTBEAT = os.path.join(STATUS_DIR, "dashboard_heartbeat.txt")

# === Heartbeat-Writer ===
def write_main_heartbeat(state="active", next_stream=None):
    data = {
        "timestamp": datetime.now().isoformat(),
        "state": state
    }

    if next_stream is not None:
        # Unterstützung für XML-Elemente und Dicts
        if hasattr(next_stream, "find"):  # ElementTree.Element
            data["next_stream"] = {
                "date": next_stream.findtext("date", ""),
                "time": next_stream.findtext("time", ""),
                "key": next_stream.findtext("key", ""),
                "title": next_stream.findtext("title", ""),
                "video_url": next_stream.findtext("video_url", "")
            }
        elif isinstance(next_stream, dict):
            data["next_stream"] = {
                "date": next_stream.get("date", ""),
                "time": next_stream.get("time", ""),
                "key": next_stream.get("key", ""),
                "title": next_stream.get("title", ""),
                "video_url": next_stream.get("video_url", "")
            }

    with open(MAIN_HEARTBEAT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def is_dashboard_alive():
    try:
        with open(DASHBOARD_HEARTBEAT, "r", encoding="utf-8") as f:
            ts = datetime.fromisoformat(f.read().strip())
        return datetime.now() - ts < timedelta(seconds=30)
    except:
        return False

# === Heartbeat Logger ===
class HeartbeatLogger:
    def __init__(self, interval_minutes=60):
        self.interval = timedelta(minutes=interval_minutes)
        self.last_logged = datetime.now()

    def maybe_log(self, note="Script läuft weiter – standby."):
        now = datetime.now()
        if now - self.last_logged >= self.interval:
            log(f"🕰️ {note}")
            self.last_logged = now

heartbeat = HeartbeatLogger()

# === CONFIG ===
with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

OBS_CONFIG = config["obs"]
PATHS = config["paths"]
stream_stats = []

# === Check ob der Prozess bereits läuft ===
def is_already_running():
    s = socket.socket()
    try:
        # Wähle einen spezifischen internen Port für den Lock
        s.bind(('127.0.0.1', 65432))
        return False
    except socket.error:
        return True

if is_already_running():
    log("⚠️ main.py läuft bereits – Doppelstart verhindert.")
    print("⚠️ main.py läuft bereits! Doppelstart wird verhindert.")
    sys.exit(1)

# === Dashboard Watchdog (Heartbeat + Prozessprüfung) ===
def is_dashboard_running():
    for proc in psutil.process_iter(attrs=["cmdline"]):
        try:
            if "dashboard_main.py" in " ".join(proc.info["cmdline"]):
                return True
        except:
            continue
    return False

def start_dashboard():
    script_path = os.path.join(BASE_DIR, "dashboard_main.py")
    subprocess.Popen([sys.executable, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def dashboard_watchdog_loop():
    while True:
        dashboard_alive = is_dashboard_running()
        heartbeat_ok = is_dashboard_alive()

        if not dashboard_alive or not heartbeat_ok:
            log("🛠️ Dashboard nicht aktiv oder eingefroren – Neustart wird vorbereitet...")

            # 🧨 Zuerst alle alten dashboard_main.py Prozesse killen
            for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
                try:
                    if "dashboard_main.py" in " ".join(proc.info["cmdline"]):
                        os.kill(proc.info["pid"], 9)
                        log(f"☠️ Alter dashboard_main.py-Prozess ({proc.info['pid']}) wurde beendet.")
                except Exception as e:
                    log(f"⚠️ Fehler beim Beenden von dashboard_main.py: {e}")

            # 🚀 Dann sauber neu starten
            start_dashboard()
            log("✅ dashboard_main.py wurde neu gestartet.")

        write_main_heartbeat("active")
        time.sleep(15)

# === Flag-Handling für saubere Beendigung ===
FLAG_PATH = os.path.join(RUNTIME_FLAGS_DIR, "main_done.flag")
if os.path.exists(FLAG_PATH):
    os.remove(FLAG_PATH)

# === YouTube Streams planen ===
def plan_future_streams():
    try:
        xml_path, events = extract_events(target_day_offset=config["web"]["target_offset_days"])
        stream_infos = create_streams(events)
        for s in stream_infos:
            si = StreamInfo(s.date, s.time, s.title, s.location, s.stream_url, s.stream_key, s.video_url)
            append_stream_to_monthly_xml(si)

        today = datetime.today().strftime("%Y-%m-%d")
        today_fmt = datetime.today().strftime("%d.%m.%y")

        if config["telegram"].get("notify_summary_start", True):
            msg = f"#Sakristei geplante Streams\n📅 {today_fmt} – Initialisierung abgeschlossen\n"
            msg += f"📦 Geplante Streams für +{config['web']['target_offset_days']} Tage: {len(stream_infos)}"
            send_telegram_message(msg)

        if config["telegram"].get("notify_next_today", True):
            today_streams = load_todays_streams_from_xml()
            msg = f"#Next\nHeute {today_fmt} geplant:\n"
            if today_streams:
                for s in sorted(today_streams, key=lambda x: x["time"]):
                    zeile = f"{s['time']} {s['title']}"
                    if s.get("video_url"):
                        zeile += f"\n{s['video_url']}"
                    msg += zeile + "\n"
            else:
                msg += "Keine Streams für heute geplant."
            send_telegram_message(msg)

        send_stream_overview_email(
            os.path.join(_abs(PATHS['youtube_output_dir']), f"youtube_streams_geplant_{today}.txt")
        )

        if config["telegram"].get("send_xml_file", True):
            sakristei_config_path = _abs(config["telegram"]["credentials_file"])
            with open(sakristei_config_path, "r", encoding="utf-8") as f:
                creds = json.load(f)
            bot_token = creds["token"]
            chat_id = creds["chat_id"]
            month_file = os.path.join(_abs(PATHS['xml_output_dir']), f"streams_{today[:7]}.xml")
            send_file_to_telegram(bot_token, chat_id, month_file, caption=f"#XML 🧾 Monatsdatei\n📂 Monats-XML {today[:7]}")
    except Exception as e:
        msg = f"#Sakristei Fehler\nFehler bei der Initialisierung: {str(e)}"
        log(msg)
        if config["telegram"].get("notify_errors", True):
            send_telegram_message(msg)

# === Tagesstreams starten ===
def handle_todays_streams():
    try:
        today = datetime.today().strftime("%Y-%m-%d")
        month_file = os.path.join(_abs(PATHS['xml_output_dir']), f"streams_{today[:7]}.xml")
        if not os.path.exists(month_file):
            log("📭 Keine geplanten Streams für heute.")
            return

        tree = ET.parse(month_file)
        root = tree.getroot()
        all_streams = [s for s in root.findall("stream") if s.find("date").text == today]
        all_streams.sort(key=lambda s: s.find("time").text)

        for stream in all_streams:
            date_str = stream.find("date").text
            time_str = stream.find("time").text
            title = stream.find("title").text
            location = stream.find("location").text
            server = stream.find("url").text
            key = stream.find("key").text

            dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            if dt < now - timedelta(minutes=OBS_CONFIG.get("stream_execution_grace_minutes", 5)):
                log(f"⏩ Stream übersprungen: {title} ({time_str}) – zu alt.")
                continue

            text_display = f"{title} – {time_str} Uhr"
            next_log = datetime.now()

            while datetime.now() < dt - timedelta(minutes=OBS_CONFIG["stream_start_offset_minutes"]):
                now = datetime.now()
                if now >= next_log:
                    wait_min = int((dt - timedelta(minutes=OBS_CONFIG["stream_start_offset_minutes"]) - now).total_seconds() / 60)
                    log(f"Warte {wait_min} Minuten bis OBS-Start...")
                    next_log = now + timedelta(minutes=30)
                heartbeat.maybe_log()
                time.sleep(60)

            start_time = datetime.now()
            obs = OBSController()
            obs.set_text(OBS_CONFIG["text_source"], text_display)
            obs.switch_scene(OBS_CONFIG["scene_start"])
            obs.set_stream_settings(server, key)
            obs.start_stream()

            while datetime.now() < dt - timedelta(minutes=OBS_CONFIG["scene_switch_offset_minutes"]):
                heartbeat.maybe_log()
                time.sleep(5)
            obs.switch_scene(OBS_CONFIG["scene_live"])

            log("⏳ Warten auf manuelles oder automatisches Stream-Ende beginnt jetzt...")
            manuell = False
            max_end_time = dt + timedelta(hours=3)

            while True:
                try:
                    status = obs.client.get_stream_status()
                    if not status.output_active:
                        manuell = True
                        log("📴 OBS meldet: Stream wurde manuell beendet.")
                        break
                except Exception as e:
                    log(f"⚠️ Fehler beim Abrufen des Streamstatus: {e}")
                    break

                if datetime.now() > max_end_time:
                    log("⏱️ Max. Laufzeit erreicht – Stream gilt als automatisch beendet.")
                    break

                heartbeat.maybe_log()
                time.sleep(60)

            end_time = datetime.now()
            stream_stats.append({
                "title": title,
                "start": start_time,
                "end": end_time,
                "duration": end_time - start_time
            })
     
            next_stream = get_next_stream()
            if next_stream is not None:
                next_stream_to_obs(next_stream)
            else:
                log("ℹ️ Kein weiterer Stream vorhanden.")

            obs.close()

    except Exception as e:
        msg = f"#Sakristei Fehler\nFehler bei der Tagesverarbeitung: {str(e)}"
        log(msg)
        if config["telegram"].get("notify_errors", True):
            send_telegram_message(msg)
    

# === MAIN ===
def main():
    log("🚀 Starte Tages-Skript für Kirchenstream")

    threading.Thread(target=dashboard_watchdog_loop, daemon=True).start()

    # Teil 1: YouTube-Planung
    try:
        plan_future_streams()
    except Exception as e:
        msg = f"#Sakristei Fehler\n❌ Fehler bei der Streamplanung (YouTube): {e}"
        log(msg)
        if config["telegram"].get("notify_errors", True):
            send_telegram_message(msg)

    # == Nächsten Tagesstream in Heartbeat sichern ==
    try:
        today_streams = load_todays_streams_from_xml()
        if today_streams:
            next_stream = sorted(today_streams, key=lambda x: x["time"])[0]
            write_main_heartbeat("active", next_stream=next_stream)
        else:
            write_main_heartbeat("active")
    except Exception as e:
        log(f"⚠️ Fehler beim Schreiben des Heartbeat-Streams: {e}")
        write_main_heartbeat("active")

    # Teil 2: Tagesstreams starten – unabhängig von YouTube
    try:
        handle_todays_streams()
    except Exception as e:
        msg = f"#Sakristei Fehler\n❌ Fehler bei der Tages-Streamverarbeitung: {e}"
        log(msg)
        if config["telegram"].get("notify_errors", True):
            send_telegram_message(msg)

    upload_streamlink_html()   # generiere und lade HTML Seite der Streams auf Strato zur Anzeige in der Pfarrei Webseite

    # Abschlussbenachrichtigung wie bisher
    if config["telegram"].get("notify_summary_end", True):
        today = datetime.today().strftime("%Y-%m-%d")
        if stream_stats:
            msg = f"#Sakristei durchgeführte Streams\n📅 {today} – Tageslauf beendet\n\n✅ {len(stream_stats)} Streams ausgeführt:\n"
            for s in stream_stats:
                start = s["start"].strftime("%H:%M")
                end = s["end"].strftime("%H:%M")
                duration = str(s["duration"]).split(".")[0]
                msg += f"• {start}–{end} Uhr – {s['title']} ({duration})\n"
        else:
            msg = f"#Sakristei durchgeführte Streams\n📅 {today} – Tageslauf beendet\n❌ Kein Stream wurde heute ausgeführt."
        send_telegram_message(msg)

    # Flag sauber schreiben (Verzeichnis existiert bereits, zur Sicherheit erneut absichern)
    os.makedirs(os.path.dirname(FLAG_PATH), exist_ok=True)
    with open(FLAG_PATH, "w", encoding="utf-8") as f:
        f.write("main.py wurde planmäßig beendet.")
    write_main_heartbeat("planned_exit")
    log("✅ Alle geplanten Streams verarbeitet. Skript beendet.")

    # Am Ende von main(), wenn kein Stream heute lief
    if not stream_stats:
        next_stream = get_next_stream()
        if next_stream is not None:
            next_stream_to_obs(next_stream)
            write_main_heartbeat("planned_exit", next_stream=next_stream)  # ⬅️ hier ergänzt
        else:
            write_main_heartbeat("planned_exit")  # ⬅️ fallback
    else:
        write_main_heartbeat("planned_exit")  # ⬅️ wenn Streams heute liefen

if __name__ == "__main__":
    main()
