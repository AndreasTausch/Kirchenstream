import os
import psutil
import subprocess
import time
import logging
from datetime import datetime, timedelta

from modules.dashboard_heartbeat import read_main_heartbeat

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def restart_main_process():
    try:
        subprocess.Popen(
            ["python", os.path.join(BASE_DIR, "..", "main.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logging.info("🚀 main.py wurde neu gestartet.")
    except Exception as e:
        logging.error(f"Fehler beim Starten von main.py: {e}")

def main_watchdog_loop():
    while True:
        try:
            state, ts = read_main_heartbeat()
            now = datetime.now()
            too_old = not ts or (now - ts > timedelta(seconds=90))
            unclean_shutdown = state != "planned_exit"

            main_running = False
            for proc in psutil.process_iter(attrs=["cmdline"]):
                try:
                    if "main.py" in " ".join(proc.info["cmdline"]):
                        main_running = True
                        break
                except:
                    continue

            if not main_running and too_old and unclean_shutdown:
                logging.warning("❌ main.py abgestürzt erkannt – Neustart wird eingeleitet...")
                for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
                    try:
                        if "main.py" in " ".join(proc.info["cmdline"]):
                            os.kill(proc.info["pid"], 9)
                            logging.warning(f"🛠️ Alter main.py-Prozess {proc.info['pid']} wurde beendet.")
                    except:
                        pass
                restart_main_process()
        except Exception as e:
            logging.error(f"Fehler im main.py-Watchdog: {e}")
        time.sleep(30)
