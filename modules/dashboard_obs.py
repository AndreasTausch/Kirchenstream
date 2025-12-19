import threading
import logging
from obswebsocket import obsws, requests as obs_requests

class OBSClient:
    def __init__(self, host="localhost", port=4455, password=""):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.lock = threading.Lock()
        self.connected = False
        self.last_scene = None

    def connect(self):
        try:
            if self.ws:
                self.ws.disconnect()
        except:
            pass
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True
            logging.info("✅ OBS WebSocket verbunden.")
        except Exception as e:
            self.connected = False
            logging.warning(f"OBS-Verbindung fehlgeschlagen: {e}")

    def get_scene(self):
        with self.lock:
            if not self.connected:
                self.connect()
                if not self.connected:
                    return None
            try:
                response = self.ws.call(obs_requests.GetCurrentProgramScene())
                self.last_scene = response.getSceneName()
                return self.last_scene
            except Exception as e:
                logging.warning(f"Fehler beim Abrufen der OBS-Szene: {e}")
                self.connected = False
                return None
