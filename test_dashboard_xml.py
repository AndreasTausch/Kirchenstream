import os
import xml.etree.ElementTree as ET
from datetime import datetime

xml = os.path.join("data", f"streams_{datetime.now().strftime('%Y-%m')}.xml")
print("XML:", xml, "exists:", os.path.exists(xml))

if os.path.exists(xml):
    root = ET.parse(xml).getroot()
    now = datetime.now()
    cands = []
    for s in root.findall("stream"):
        dt = datetime.strptime(s.find("date").text + " " + s.find("time").text, "%Y-%m-%d %H:%M")
        title = s.find("title").text
        vid = (s.find("video_url").text or "").strip()
        if dt > now:
            cands.append((dt, title, vid))
    cands.sort(key=lambda x: x[0])
    print("Kandidaten:", len(cands))
    for dt, title, vid in cands[:3]:
        print(" ->", dt, title, vid)
