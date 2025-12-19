import os
import sys
import time
import threading
import logging
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import socketserver

# === Pfade setzen ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULES_DIR = os.path.join(BASE_DIR, "modules")
sys.path.insert(0, MODULES_DIR)

# === Logging einrichten ===
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"dashboard_{datetime.now().strftime('%Y-%m')}.log")
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# === Imports der Module ===
from modules.dashboard_obs import OBSClient
from modules.dashboard_status import update_status
from modules.dashboard_html import HTML_OUTPUT_PATH
from modules.dashboard_heartbeat import write_dashboard_heartbeat
from modules.dashboard_watchdog import main_watchdog_loop

PORT = 5000

# === SERVER ===

def start_dashboard():
    class CustomHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                for _ in range(3):
                    try:
                        with open(HTML_OUTPUT_PATH, "rb") as f:
                            content = f.read()
                        break
                    except Exception:
                        time.sleep(0.2)
                else:
                    logging.error("❌ Fehler beim Lesen der HTML-Datei:", exc_info=True)
                    self.send_error(500, "Fehler beim Lesen der HTML-Datei")
                    return

                try:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.send_header("Content-length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception:
                    logging.error("❌ Fehler beim Senden der HTML-Antwort:", exc_info=True)
                    self.send_error(500, "Fehler beim Senden der HTML-Antwort")
            else:
                self.send_error(404, "Nicht gefunden")

        def log_message(self, format, *args):
            return

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler)

    def run_webserver():
        try:
            httpd.serve_forever()
        except Exception:
            logging.error("❌ Fehler im Webserver-Thread", exc_info=True)

    def run_updater():
        while True:
            try:
                update_status()
                write_dashboard_heartbeat()
                time.sleep(10)
            except Exception:
                logging.error("❌ Fehler im Updater-Thread", exc_info=True)

    threading.Thread(target=run_webserver, daemon=True).start()
    threading.Thread(target=run_updater, daemon=True).start()
    threading.Thread(target=main_watchdog_loop, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        httpd.shutdown()
        logging.info("🔌 Dashboard-Server manuell beendet.")

# === ENTRYPOINT ===
if __name__ == "__main__":
    start_dashboard()
