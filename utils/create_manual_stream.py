"""
Skript: create_manual_stream.py
Zweck: Erzeugt einen YouTube-Livestream auf Basis eines manuell angelegten XML-Eintrags 
       und fügt ihn in die Monats-XML ein, damit OBS ihn später automatisch nutzen kann.

Voraussetzung:
- Eine XML-Datei im Format extrahierte_termine/extrahierte_termine_YYYY-MM-DD.xml
  mit mindestens einem <event>-Eintrag (Datum, Uhrzeit, Titel, Ort).
- Der Titel muss ein Stichwort wie "YT" enthalten, damit das YouTube-Modul ihn akzeptiert.
- OBS Studio muss separat mit main.py oder handle_todays_streams() gestartet werden.

Wichtig:
- Achte darauf, dass <date> in der XML dem heutigen Datum entspricht,
  wenn der Stream noch am selben Tag über OBS automatisch gestartet werden soll.
- Für ein anderes Datum:
    → passe den Dateinamen in Zeile 39 an
    → passe das Datum im <date>-Feld innerhalb der XML an
"""

import xml.etree.ElementTree as ET
from modules.youtube_manager import create_streams
from modules.xml_writer import StreamInfo, append_stream_to_monthly_xml
from datetime import datetime

def parse_events(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    events = []
    for e in root.findall("event"):
        events.append(type("Event", (), {
            "date": e.find("date").text,
            "time": e.find("time").text,
            "title": e.find("title").text,
            "location": e.find("location").text
        })())
    return events

if __name__ == "__main__":
    xml_path = "extrahierte_termine/extrahierte_termine_2025-05-30.xml"
    events = parse_events(xml_path)
    streams = create_streams(events)
    for s in streams:
        si = StreamInfo(s.date, s.time, s.title, s.location, s.stream_url, s.stream_key)
        append_stream_to_monthly_xml(si)
