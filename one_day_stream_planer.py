from datetime import datetime, timedelta
from modules.web_parser import extract_events
from modules.youtube_manager import create_streams
from modules.xml_writer import StreamInfo, append_stream_to_monthly_xml
from modules.mail_sender import send_stream_overview_email
from utils.logger import log
import os

def plan_stream_for_single_day(x=7):
    """
    Plan YouTube streams only for one specific day offset x (e.g., x=3 means 3 days from today).
    """
    log(f"🚀 Starte Einzelplanung für Tag +{x} ab heute.")

    try:
        xml_path, events = extract_events(target_day_offset=x)
        log(f"📅 Tag +{x}: {len(events)} relevante Termine gefunden.")

        stream_infos = create_streams(events)
        for s in stream_infos:
            si = StreamInfo(s.date, s.time, s.title, s.location, s.stream_url, s.stream_key)
            append_stream_to_monthly_xml(si)

        # 📧 E-Mail-Versand für diesen Tag
        day = (datetime.today() + timedelta(days=x)).strftime("%Y-%m-%d")
        mail_txt_path = os.path.join("youtube_streams_geplant", f"youtube_streams_geplant_{day}.txt")
        send_stream_overview_email(mail_txt_path)

        log(f"✅ Planung abgeschlossen für Tag +{x}.")

    except Exception as e:
        log(f"❌ Fehler an Tag +{x}: {e}")

if __name__ == "__main__":
    plan_stream_for_single_day(x=7)  # <== hier gewünschten Tag-Offset eintragen