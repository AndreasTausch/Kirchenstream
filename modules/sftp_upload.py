import os
import json
import paramiko
from datetime import datetime

def upload_file_via_sftp(local_path, remote_path):
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        SECRETS_PATH = os.path.join(BASE_DIR, "..", "secrets", "strato_upload.json")

        with open(SECRETS_PATH, "r", encoding="utf-8") as f:
            creds = json.load(f)

        host = creds["host"]
        port = creds["port"]
        username = creds["username"]
        password = creds["password"]

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.put(local_path, remote_path)
        sftp.close()
        transport.close()

        print(f"✅ Datei erfolgreich hochgeladen: {local_path} → {remote_path}")

        log_path = os.path.join(os.path.dirname(__file__), "uploadlog.txt")
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Upload erfolgreich: {local_path} → {remote_path}\n")

        return True

    except Exception as e:
        print(f"❌ Fehler beim SFTP-Upload: {e}")
        log_path = os.path.join(os.path.dirname(__file__), "uploadlog.txt")
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Fehler beim Upload: {e}\n")
        return False
