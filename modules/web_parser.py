import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
import time
import yaml
import xml.etree.ElementTree as ET

from utils.logger import log
from utils.cookie_handler import handle_cookie_banner

# === Konfiguration sicher laden relativ zu Skriptpfad ===
base_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(base_dir, ".."))
with open(os.path.join(root_dir, "config.yaml"), "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
WEB_CONFIG = config["web"]

class Event:
    def __init__(self, date, time_str, title, location):
        self.date = date
        self.time = time_str
        self.title = title
        self.location = location

    def to_xml_element(self):
        e = ET.Element("event")
        ET.SubElement(e, "date").text = self.date
        ET.SubElement(e, "time").text = self.time
        ET.SubElement(e, "title").text = self.title
        ET.SubElement(e, "location").text = self.location
        return e

def _make_visible_driver():
    """Chrome mit GUI starten (kein Headless), Fenster bleibt offen."""
    options = Options()
    # WICHTIG: Sichtbar machen
    # KEIN --headless
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    # Fenster nach Scriptende nicht sofort schließen (praktisch zum Debuggen)
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Versuch 1: Selenium-Manager (keine separate Treiber-Installation nötig)
    try:
        return webdriver.Chrome(options=options)
    except Exception as e1:
        log(f"ℹ️ Selenium-Manager Start fehlgeschlagen, fallback webdriver_manager: {e1}")
        # Versuch 2: webdriver_manager
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

def extract_events(target_day_offset=None, output_dir="extrahierte_termine"):
    if target_day_offset is None:
        target_day_offset = WEB_CONFIG["target_offset_days"]

    ziel_datum = datetime.today() + timedelta(days=target_day_offset)
    ziel_str = ziel_datum.strftime("%Y-%m-%d")
    url = (
        "https://pfarrverband-waldkirchen.bistum-passau.de/aktuelles-termine/gottesdienste"
        f"?startDate={ziel_str}&endDate={ziel_str}&church={WEB_CONFIG['church_id']}"
    )

    log(f"Zieltags-Datum: {ziel_str}")
    log(f"URL aufgerufen: {url}")

    # Sichtbarer Chrome
    driver = _make_visible_driver()
    events = []

    try:
        driver.get(url)
        time.sleep(3)
        handle_cookie_banner(driver)   # hier interagierst Du sichtbar mit dem Banner
        time.sleep(2)

        entries = driver.find_elements(By.CLASS_NAME, "m-churchServiceListItem")
        log(f"{len(entries)} Gottesdienst-Einträge gefunden.")

        for entry in entries:
            try:
                left = entry.find_element(By.CLASS_NAME, "m-churchServiceListItem__left")
                right = entry.find_element(By.CLASS_NAME, "m-churchServiceListItem__right")

                left_text = " ".join(left.text.strip().splitlines())
                right_lines = right.text.strip().split("\n")

                title = right_lines[0].strip() if len(right_lines) > 0 else ""
                church = right_lines[1].strip() if len(right_lines) > 1 else ""

                if any(keyword in title.lower() for keyword in WEB_CONFIG["keywords"]):
                    parts = left_text.split(", ")
                    datum_roh = parts[0].split()[0]
                    uhrzeit = parts[1].split(" Uhr")[0].strip()

                    tag, monat = datum_roh.split(".")
                    datum_final = f"{ziel_datum.year}-{monat.zfill(2)}-{tag.zfill(2)}"

                    events.append(Event(
                        date=datum_final,
                        time_str=uhrzeit,
                        title=title,
                        location=church
                    ))

                    log(f"✅ Termin übernommen: {datum_final} {uhrzeit} - {title} ({church})")
                else:
                    log(f"ℹ️ Termin ignoriert: {title}")
            except Exception as e:
                log(f"⚠️ Fehler beim Parsen eines Eintrags: {e}")

    except Exception as e:
        log(f"❌ Fehler beim Seitenaufruf oder Cookie-Handling: {e}")
    finally:
        # NICHT quit() aufrufen, damit das Fenster sichtbar bleibt, solange Du willst.
        # Zum produktiven Betrieb ohne GUI wieder driver.quit() aktivieren.
        pass
        driver.quit()

    # Ausgabeordner WD-unabhängig relativ zum Projekt
    out_dir_abs = output_dir if os.path.isabs(output_dir) else os.path.join(root_dir, output_dir)
    os.makedirs(out_dir_abs, exist_ok=True)
    xml_filename = os.path.join(out_dir_abs, f"extrahierte_termine_{ziel_str}.xml")
    write_events_to_xml(events, xml_filename)
    return xml_filename, events

def write_events_to_xml(events, path):
    root = ET.Element("events")
    for event in events:
        root.append(event.to_xml_element())
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    log(f"✅ XML-Datei gespeichert unter '{path}'")

if __name__ == "__main__":
    filename, extracted = extract_events()
    print(f"✅ XML-Datei geschrieben: {filename}")
    print(f"{len(extracted)} relevante Termine extrahiert.")
