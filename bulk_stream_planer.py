import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime, timedelta
from modules.web_parser import extract_events
from modules.youtube_manager import create_streams
from modules.xml_writer import StreamInfo, append_stream_to_monthly_xml
from utils.logger import log


def bulk_plan_streams(tage=10):
    log(f"🚀 Starte Batch-Planung für {tage} Tage ab heute.")

    all_streams = []
    for offset in range(tage):
        try:
            xml_path, events = extract_events(target_day_offset=offset)
            log(f"📅 Tag +{offset}: {len(events)} relevante Termine gefunden.")

            stream_infos = create_streams(events)
            for s in stream_infos:
                si = StreamInfo(s.date, s.time, s.title, s.location, s.stream_url, s.stream_key, s.video_url)
                append_stream_to_monthly_xml(si)

        except Exception as e:
            log(f"❌ Fehler an Tag +{offset}: {e}")

    log(f"✅ Batch abgeschlossen. Insgesamt {len(all_streams)} Streams geplant.")
    return all_streams

if __name__ == "__main__":
    bulk_plan_streams(tage=10)
