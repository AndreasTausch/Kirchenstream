from datetime import datetime, timedelta
from utils.logger import log

class HeartbeatLogger:
    def __init__(self, interval_minutes=60):
        self.interval = timedelta(minutes=interval_minutes)
        self.last_logged = datetime.now()

    def maybe_log(self, note="Script läuft weiter – standby."):
        now = datetime.now()
        if now - self.last_logged >= self.interval:
            log(f"🕰️ {note}")
            self.last_logged = now
