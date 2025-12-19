# modules/stream_info.py
import xml.etree.ElementTree as ET

class StreamInfo:
    def __init__(self, date, time, title, location, stream_url, stream_key, video_url):
        self.date = date
        self.time = time
        self.title = title
        self.location = location
        self.stream_url = stream_url
        self.stream_key = stream_key
        self.video_url = video_url
    def to_log_lines(self):
        return [
            f"📅 Datum: {self.date}",
            f"🕒 Uhrzeit: {self.time}",
            f"📌 Titel: {self.title}",
            f"📍 Ort: {self.location}",
            f"🔗 Video-URL: {self.video_url}",
            f"📡 Stream-URL: {self.stream_url}",
            f"🗝️ Stream-Key: {self.stream_key}"
        ]

    def to_xml_element(self):
        e = ET.Element("stream")
        ET.SubElement(e, "date").text = self.date
        ET.SubElement(e, "time").text = self.time
        ET.SubElement(e, "title").text = self.title
        ET.SubElement(e, "location").text = self.location
        ET.SubElement(e, "url").text = self.stream_url
        ET.SubElement(e, "key").text = self.stream_key
        ET.SubElement(e, "video_url").text = self.video_url
        return e
