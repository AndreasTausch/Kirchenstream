import sys
import os
import time
import json
import yaml
from obsws_python import ReqClient
from utils.logger import log

# === Projektpfad einfügen ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# === Konfiguration laden ===
base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "..", "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
OBS_CONFIG = config["obs"]

credentials_path = os.path.join(base_dir, "..", OBS_CONFIG["password_file"])
with open(credentials_path, "r", encoding="utf-8") as f:
    secrets = json.load(f)

def next_stream_to_obs(next_stream):
    try:
        next_title = next_stream.find("title").text
        next_time = next_stream.find("time").text
        next_server = next_stream.find("url").text
        next_key = next_stream.find("key").text
        next_video_url = next_stream.find("video_url").text or "-"

        text_display = f"{next_title} – {next_time} Uhr"

        obs = OBSController()
        obs.set_text(OBS_CONFIG["text_source"], text_display)
        obs.set_stream_settings(next_server, next_key)
        obs.switch_scene(OBS_CONFIG["scene_start"])  # optional
        obs.close()

        log(f"🛠️ OBS konfiguriert:\n• {next_title} ({next_time})\n🗝️ {next_key}\n🔗 {next_video_url}")
        return True
    except Exception as e:
        log(f"⚠️ Fehler bei OBS-Vorbereitung: {e}")
        return False

class OBSController:
    def __init__(self):
        try:
            self.client = ReqClient(
                host=OBS_CONFIG["host"],
                port=OBS_CONFIG["port"],
                password=secrets["password"]
            )
            log("🔐 Verbindung zu OBS-WebSocket (v5) hergestellt.")
        except Exception as e:
            log(f"❌ Fehler beim Verbinden mit OBS: {e}")
            raise

    def set_text(self, source_name, new_text):
        formatted_text = new_text.replace(" – ", "\n")  # Titel und Uhrzeit umbrechen
        settings = {
            "text": formatted_text,
            "font": {
                "face": "Segoe UI",
                "size": 100,
                "style": "Bold"
            },
            "color1": 0xFF00B3B0,  # Schriftfarbe (#00b3b0) + 100% Deckkraft (Alpha FF)
            "alignment": 2,        # Mitte oben (zentriert)
            "bk_color": 0x00FFFFFF,  # Hintergrund weiß, 0% Deckkraft (Alpha 00)
            "outline": True,
            "outline_size": 2,
            "outline_color": 0xFFFFFFFF  # Weiß, volle Deckkraft
        }
        self.client.set_input_settings(source_name, settings, overlay=False)
        log(f"📝 Textquelle '{source_name}' aktualisiert mit: {formatted_text}")

    def switch_scene(self, scene_name):
        self.client.set_current_program_scene(scene_name)
        log(f"🎬 Szene gewechselt zu: {scene_name}")

    def set_stream_settings(self, server, key):
        try:
            log(f"🌐 Setze Stream-Server: {server}, Key: {'[vorhanden]' if key else '[leer]'}")
            self.client.set_stream_service_settings(
                "rtmp_custom",
                {
                    "server": server,
                    "key": key,
                    "use_auth": False
                }
            )
            time.sleep(2)  # OBS braucht kurze Zeit zum Setzen der Übertragung
            result = self.client.get_stream_service_settings()
            current_type = result.stream_service_type
            current_data = result.stream_service_settings
            current_server = current_data.get("server") or ""
            current_key = current_data.get("key") or ""

            if current_type != "rtmp_custom":
                log("❌ Überprüfung: Falscher Typ gesetzt.")
            elif current_server != server:
                log(f"❌ Überprüfung: Server stimmt nicht überein (erwartet: {server}, erhalten: {current_server})")
            elif current_key != key:
                log("❌ Überprüfung: Key stimmt nicht überein.")
            else:
                log("✅ Stream-Einstellungen korrekt übernommen.")

        except Exception as e:
            log(f"❌ Fehler beim Setzen oder Überprüfen der Stream-Einstellungen: {e}")

    def start_stream(self):
        try:
            self.client.start_stream()
            log("📡 Befehl zum Starten des Streams wurde gesendet.")
            time.sleep(2)
            status = self.client.get_stream_status()
            if status.output_active:
                log("✅ OBS meldet: Stream läuft tatsächlich.")
            else:
                log("❌ OBS meldet: Stream wurde NICHT gestartet.")
        except Exception as e:
            log(f"❌ Fehler beim Starten des Streams: {e}")

    def close(self):
        self.client.disconnect()
        log("🔌 Verbindung zu OBS geschlossen.")

# === Testweise ausführen ===
if __name__ == "__main__":
    obs = OBSController()
    obs.set_text("Titel", "Teststream – 10:00 Uhr")
    obs.switch_scene("Beginn")
    obs.set_stream_settings("rtmp://x.rtmp.youtube.com/live2", "8zz5-tv1a-qmjg-7b27-eusb")
    time.sleep(10)
    obs.switch_scene("Gottesdienst")
    obs.close()
