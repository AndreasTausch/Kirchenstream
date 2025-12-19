import http.server
import socketserver
import threading
import os
import time
import xml.etree.ElementTree as ET
import json
import requests
import traceback
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PORT = 5000
XML_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TELEGRAM_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "secrets", "telegram_stgisela.json")
YOUTUBE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "secrets", "token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

confirmed_live_ids = set()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"de\">
<head>
    <meta charset=\"UTF-8\">
    <title>Kirchenstream Status</title>
    <meta http-equiv=\"refresh\" content=\"10\">
    <style>
        body {{
            background-color: #121212;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .row {{
            margin-bottom: 12px;
            padding: 8px;
            border-bottom: 1px solid #333;
        }}
        .label {{
            font-size: 12px;
            color: #999999;
        }}
        .status {{
            font-weight: bold;
            font-size: 18px;
            display: block;
        }}
        .green {{ color: #4CAF50; }}
        .yellow {{ color: #FFD700; }}
        .red {{ color: #FF5555; }}
        .gray {{ color: #888888; }}
        a {{ color: #4FC3F7; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class=\"row\"><span class=\"label\">Titel</span><br><span class=\"status\">📌 {title}</span></div>
    <div class=\"row\"><span class=\"label\">Stream Key</span><br><span class=\"status\">🗝️ {key}</span></div>
    <div class=\"row\"><span class=\"status\">🔗 <a href=\"{video_url}\" target=\"_blank\">YouTube-Link öffnen</a></span></div>
    <div class=\"row\"><span class=\"status {status_color}\">{status_text}</span></div>
    <div class=\"row\"><span class=\"status {camera_hint_color}\">{camera_hint}</span></div>
    <div class=\"row\"><span class=\"status {remote_color}\">📶 Status St. Gisela</span></div>
</body>
</html>
"""

def get_youtube_livestatus(broadcast_id):
    try:
        creds = Credentials.from_authorized_user_file(YOUTUBE_TOKEN_PATH, SCOPES)
        youtube = build("youtube", "v3", credentials=creds)
        request = youtube.liveBroadcasts().list(part="status", id=broadcast_id)
        response = request.execute()
        if not response["items"]:
            return None
        return response["items"][0]["status"]["lifeCycleStatus"]
    except:
        return None

class DynamicHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            try:
                today = datetime.today().strftime("%Y-%m-%d")
                month = today[:7]
                xml_path = os.path.join(XML_DIR, f"streams_{month}.xml")
                title = "-"
                key = "-"
                video_url = "#"
                status_text = "Kein geplanter Stream"
                status_color = "gray"
                remote_color = "gray"
                camera_hint = "Automatik Modus"
                camera_hint_color = "red"

                next_stream = None
                if os.path.exists(xml_path):
                    try:
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        future = []
                        now = datetime.now()
                        for s in root.findall("stream"):
                            stream_date = s.find("date").text
                            stream_time = s.find("time").text
                            try:
                                dt = datetime.strptime(f"{stream_date} {stream_time}", "%Y-%m-%d %H:%M")
                                if now - timedelta(minutes=5) <= dt <= now + timedelta(hours=2):
                                    future.append((dt, s))
                            except Exception as e:
                                print(f"⚠️ Fehler beim Parsen von Datum/Zeit: {stream_date} {stream_time} – {e}")
                                continue
                        if future:
                            next_stream = sorted(future, key=lambda x: x[0])[0][1]
                    except Exception as e:
                        print("❌ Fehler beim Verarbeiten der XML-Datei:")
                        traceback.print_exc()

                if next_stream is not None:
                    try:
                        title = next_stream.find("title").text
                        key = next_stream.find("key").text
                        video_url = next_stream.find("video_url").text or "#"
                        broadcast_id = video_url.split("/")[-1] if video_url else "-"

                        stream_date = next_stream.find("date").text
                        stream_time = next_stream.find("time").text
                        sched_dt = datetime.strptime(f"{stream_date} {stream_time}", "%Y-%m-%d %H:%M")
                        now = datetime.now()
                        obs_start_dt = sched_dt - timedelta(minutes=6)
                        delta = (obs_start_dt - now).total_seconds()

                        yt_status = get_youtube_livestatus(broadcast_id) if broadcast_id else None
                        if yt_status == "live":
                            confirmed_live_ids.add(broadcast_id)

                        if broadcast_id in confirmed_live_ids:
                            status_text = "✅ Stream läuft"
                            status_color = "green"
                            if now >= sched_dt:
                                camera_hint = "📷 Bitte Kamerakontrolle übernehmen"
                                camera_hint_color = "yellow"
                            else:
                                camera_hint = "Automatik Modus"
                                camera_hint_color = "red"
                        elif delta > 0:
                            status_text = f"⏳ {int(delta // 60)} Minuten bis Streamstart"
                            status_color = "white"
                        elif -120 <= delta <= 0:
                            status_text = "⏳ Warte auf YouTube..."
                            status_color = "white"
                        elif -900 <= delta < -120:
                            status_text = "✅ Stream läuft (vermutlich)"
                            status_color = "green"
                            if now >= sched_dt:
                                camera_hint = "📷 Bitte Kamerakontrolle übernehmen"
                                camera_hint_color = "yellow"
                            else:
                                camera_hint = "Automatik Modus"
                                camera_hint_color = "red"
                        else:
                            status_text = "🔴 Stream beendet – Overlay schließt in 10 Min"
                            status_color = "yellow"
                    except Exception as e:
                        print("❌ Fehler beim Verarbeiten des nächsten Streams:")
                        traceback.print_exc()

                try:
                    with open(TELEGRAM_CREDENTIALS_PATH, "r", encoding="utf-8") as f:
                        creds = json.load(f)
                    bot_token = creds["token"]
                    chat_id = creds["chat_id"]
                    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        messages = data.get("result", [])[::-1]
                        for msg in messages:
                            if "message" in msg and str(msg["message"].get("chat", {}).get("id")) == str(chat_id):
                                text = msg["message"].get("text", "")
                                if text.startswith("#On"):
                                    remote_color = "green"
                                elif text.startswith("#Off"):
                                    remote_color = "gray"
                                break
                except Exception as e:
                    print("❌ Fehler beim Abrufen des Telegram-Status:")
                    traceback.print_exc()

                html = HTML_TEMPLATE.format(
                    title=title,
                    key=key,
                    video_url=video_url,
                    status_text=status_text,
                    status_color=status_color,
                    remote_color=remote_color,
                    camera_hint=camera_hint,
                    camera_hint_color=camera_hint_color
                ).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html)

            except Exception as e:
                print("❌ Unerwarteter Fehler im Dashboard:")
                traceback.print_exc()

        else:
            super().do_GET()

def start_server():
    os.chdir(os.path.dirname(__file__))
    handler = DynamicHandler
    try:
        with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
            print(f"🟢 Dashboard läuft auf http://localhost:{PORT}/")
            httpd.serve_forever()
    except OSError as e:
        print(f"❌ Portfehler: {e}")

if __name__ == "__main__":
    start_server()
