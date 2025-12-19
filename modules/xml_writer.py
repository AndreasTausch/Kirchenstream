import os
import xml.etree.ElementTree as ET
from datetime import datetime
from modules.stream_info import StreamInfo
from utils.logger import log

XML_DIR = "data"

def load_todays_streams_from_xml():
    today = datetime.today().strftime("%Y-%m-%d")
    month_file = os.path.join(XML_DIR, f"streams_{today[:7]}.xml")
    if not os.path.exists(month_file):
        return []

    tree = ET.parse(month_file)
    root = tree.getroot()
    return [
        {
            "date": s.find("date").text,
            "time": s.find("time").text,
            "title": s.find("title").text,
            "location": s.find("location").text,
            "url": s.find("url").text,
            "key": s.find("key").text,
            "video_url": s.find("video_url").text if s.find("video_url") is not None else ""
        }
        for s in root.findall("stream")
        if s.find("date").text == today
    ]

def append_stream_to_monthly_xml(stream_info):
    month_str = stream_info.date[:7]  # YYYY-MM
    filename = f"streams_{month_str}.xml"
    filepath = os.path.join(XML_DIR, filename)
    os.makedirs(XML_DIR, exist_ok=True)

    if os.path.exists(filepath):
        tree = ET.parse(filepath)
        root = tree.getroot()

        for stream in root.findall("stream"):
            if (
                stream.find("date").text == stream_info.date and
                stream.find("time").text == stream_info.time and
                stream.find("title").text == stream_info.title
            ):
                log(f"⚠️ XML: Duplikat bereits vorhanden – {stream_info.date} {stream_info.time} {stream_info.title}")
                return
    else:
        root = ET.Element("streams")
        tree = ET.ElementTree(root)

    root.append(stream_info.to_xml_element())
    tree.write(filepath, encoding="utf-8", xml_declaration=True)
    log(f"📦 Stream in Monats-XML gespeichert: {filepath}")

if __name__ == "__main__":
    dummy = StreamInfo(
        date="2025-05-29",
        time="10:00",
        title="Pfarrgottesdienst - YT",
        location="Pfarrkirche Waldkirchen",
        stream_url="rtmp://x.rtmp.youtube.com/live2",
        stream_key="8zz5-tv1a-qmjg-7b27-eusb",
        video_url="https://youtube.com/live/ic8gy_xhGoY"
    )
    append_stream_to_monthly_xml(dummy)
