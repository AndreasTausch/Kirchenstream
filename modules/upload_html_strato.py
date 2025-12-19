import os
import json
from glob import glob
from xml.etree import ElementTree as ET
from datetime import datetime, date, timedelta
from modules.sftp_upload import upload_file_via_sftp

def upload_streamlink_html():
    # === KONFIGURATION LADEN ===
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    secrets_path = os.path.join(base_dir, "secrets", "strato_upload.json")
    with open(secrets_path, "r", encoding="utf-8") as f:
        creds = json.load(f)

    remote_target = creds["remote_path"]

    # === LOKALE ZIELDATEIEN ===
    upload_filename = "Streamlink_upload.html"

    # === ARBEITSVERZEICHNIS SETZEN ===
    working_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(working_dir)

    # === PASSENDE XML-DATEIEN FINDEN ===
    base_dir = os.path.abspath(os.path.join(working_dir, ".."))
    data_dir = os.path.join(base_dir, "data")
    all_xml_files = sorted(glob(os.path.join(data_dir, "streams_*.xml")), reverse=True)
    if len(all_xml_files) < 1:
        raise FileNotFoundError("Keine streams_YYYY-MM.xml-Dateien gefunden.")

    current_month = datetime.today().strftime("%Y-%m")
    previous_month = (datetime.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    current_file = next((f for f in all_xml_files if current_month in f), None)
    previous_file = next((f for f in all_xml_files if previous_month in f), None)

    if not current_file:
        raise FileNotFoundError(f"Keine Datei für aktuellen Monat ({current_month}) gefunden.")

    # === XML-EINTRÄGE PARSEN ===
    def parse_streams(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        entries = []
        for stream in root.findall("stream"):
            stream_date = stream.find("date").text
            stream_time = stream.find("time").text
            title = stream.find("title").text
            video_url = stream.find("video_url").text
            dt = datetime.strptime(f"{stream_date} {stream_time}", "%Y-%m-%d %H:%M")
            entries.append((dt, title, stream_date, stream_time, video_url))
        return entries

    entries = parse_streams(current_file)

    if previous_file:
        prev_entries = parse_streams(previous_file)
        prev_entries = sorted(prev_entries)[-5:]  # Letzte 5
        entries = prev_entries + entries

    entries.sort(reverse=True)

    # === HTML GENERIEREN ===
    today = date.today()
    html_parts = ['<!-- BEGIN LISTE DER STREAMS -->']

    for dt, title, stream_date, stream_time, video_url in entries:
        stream_dt = dt.date()
        if stream_dt < today:
            icon = "⏳"
        elif stream_dt == today:
            icon = "🔴"
        else:
            icon = "📅"

        html_parts.append(f"""
      <div style=\"margin-bottom: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 8px;\">
        <div style=\"display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;\">
          <h3 style=\"margin: 0;\">{icon} {title}</h3>
          <a href=\"{video_url}\" target=\"_blank\" style=\"font-size: 0.9em;\">🔗 Zum Livestream</a>
        </div>
        <div style=\"font-size: 0.9em; color: #666;\">{stream_date} – {stream_time} Uhr</div>
      </div>
    """)

    html_parts.append("<!-- ENDE LISTE DER STREAMS -->")

    # === DATEIEN SPEICHERN ===
    today_str = datetime.today().strftime("%Y%m%d")
    dated_filename = f"{today_str}_{os.path.basename(current_file)}.html"

    with open(dated_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    with open(upload_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"✅ HTML-Dateien erstellt:\n- {dated_filename}\n- {upload_filename}")

    # === SFTP-UPLOAD mit externem Modul ===
    upload_file_via_sftp(upload_filename, remote_target)

if __name__ == "__main__":
    upload_streamlink_html()
