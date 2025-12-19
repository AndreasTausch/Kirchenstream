# Kirchenstream – Automatisierte YouTube-Streamingsteuerung für Gottesdienste

Dieses Projekt automatisiert die komplette Planung, Erstellung und Durchführung von YouTube-Livestreams für Gottesdienste. Es wurde entwickelt für den Einsatz im Pfarrverband Waldkirchen und kombiniert Webseitenanalyse, YouTube-API, Telegram-/E-Mail-Benachrichtigung und OBS-Automatisierung.

---

## 🔧 Hauptfunktionen

- **Terminextraktion**: Gottesdienste für einen festgelegten Zieltag (z. B. in 7 Tagen) werden von der Webseite extrahiert.
- **Livestream-Erstellung**: Für jeden relevanten Termin wird per YouTube API ein Broadcast + Stream angelegt.
- **Kommunikation**:
  - Zusammenfassungen per E-Mail und Telegram (2 Bots)
  - Versand der XML-Monatsdatei über Telegram (Sakristei)
- **OBS-Steuerung**:
  - Vorab: Titel setzen, Szene wählen, RTMP konfigurieren
  - 5 Min vorher: Startszene & Streamstart
  - 1 Min vorher: Szenenwechsel zu Gottesdienst
  - Nach Ende: automatische oder manuelle Erkennung & Logging
- **Duplikaterkennung**: Bereits vorhandene Streams werden übersprungen (lokal + YouTube)
- **Logging**: Herzschlag-Protokollierung während der Standby-Zeit verhindert Inaktivitäts-Abbrüche durch Windows.
- **GUI**: Die Datei `config_editor.py` erlaubt einfache Bearbeitung aller Konfigurationen und Zugangsdaten.

---

## 📂 Projektstruktur

```text
kirchenstream/
├── main.py                        # Hauptsteuerungsskript (automatisch um 3:00 Uhr ausführen)
├── config.yaml                    # Konfiguration (Pfadstruktur, OBS-Szenen, Bots, Optionen)
├── config_editor.py              # GUI zur Konfiguration & Secrets-Verwaltung
├── requirements.txt              # Python-Abhängigkeiten
├── logs/                         # Logdateien (Streamverlauf, Fehler)
├── data/                         # Monatsweise XML-Archivierung der Streams
├── youtube_streams_geplant/      # Textzusammenfassungen pro Tag
├── secrets/                      # Zugangsdaten (NICHT in Versionsverwaltung einchecken!)
│   ├── obs_credentials.json
│   ├── mail_credentials.json
│   ├── telegram_credentials.json
│   └── telegram_anzeige.json
├── modules/
│   ├── web_parser.py             # Termin-Extraktion (Selenium-basiert)
│   ├── youtube_manager.py        # YouTube-API zur Broadcast/Stream-Erstellung
│   ├── mail_sender.py            # Versand von E-Mail-Übersichten
│   ├── telegram_sender.py        # Versand an zwei Telegram-Bots gleichzeitig
│   ├── telegram_file_sender.py   # XML-Dateiversand an Telegram-Bot
│   ├── obs_controller.py         # OBS-WebSocket-Steuerung (Stream starten, Text setzen, Szenen wechseln)
│   ├── xml_writer.py             # Speicherung der erstellten Streams in Monats-XML
│   └── stream_info.py            # Datenstruktur für geplante Streams
└── utils/
    └── logger.py                 # Standardisiertes Logging-Modul
```

---

## 🧠 Modulübersicht

### `web_parser.py`

- Extrahiert per Selenium relevante Gottesdienste von der Pfarreiwebseite
- Nutzt Schlüsselwörter zur Filterung (z. B. „youtube“, „stream“)
- Erstellt eine XML-Datei mit gefundenen Terminen

### `youtube_manager.py`

- Erstellt YouTube-Broadcasts & RTMP-Streams über die YouTube API
- Bindet beide Elemente zusammen
- Prüft auf doppelte Einträge in XML & auf YouTube
- Gibt StreamInfo-Objekte + TXT-Logdatei aus

### `mail_sender.py`

- Sendet Tageszusammenfassung der geplanten Streams per E-Mail

### `telegram_sender.py`

- Sendet Textnachrichten an zwei Telegram-Bots (Sakristei & Anzeige)

### `telegram_file_sender.py`

- Sendet XML-Dateien an den Telegram-Bot "Sakristei" als Dokument

### `obs_controller.py`

- Verbindet sich per WebSocket mit OBS
- Setzt Szenen, Textquellen, Streamdaten (RTMP)
- Startet & überwacht Stream
- Erkennt Stream-Ende manuell oder automatisch (max. 3h)

### `xml_writer.py`

- Schreibt alle erstellten Streams in eine Monats-XML-Datei
- Erkennt doppelte Einträge und ignoriert sie

### `stream_info.py`

- Datenmodell für geplante Streams (inkl. Datum, Uhrzeit, Titel, Video-URL)

---

## 🖥️ GUI: `config_editor.py`

```bash
python config_editor.py
```

Ermöglicht Setzen aller Parameter und Zugangsdaten:

- Telegram-Optionen (Start/Ende/Übersicht/Fehler)
- Zwei Telegram-Bots: Sakristei & Anzeige
- E-Mail-Aktivierung & Zugang
- OBS WebSocket Passwort

Die Änderungen werden direkt in `config.yaml` und den entsprechenden `secrets/*.json` gespeichert.

---

## 🧪 Konfiguration prüfen

```bash
python check_config.py
```

Dieses Tool prüft, ob alle erforderlichen Parameter in `config.yaml` und `secrets/*.json` vollständig und korrekt angegeben sind.

---

## 📦 .exe-Erstellung (optional)

```bash
pyinstaller config_editor.py --noconsole --onefile
```

Das erzeugt eine `config_editor.exe` unter `dist/`, die auf jedem Windows-Rechner lauffähig ist (ohne Python).

---

## 📆 Tagesautomatisierung

Das Skript `main.py` wird täglich um **03:00 Uhr** gestartet (Windows Aufgabenplaner).

1. **Planung für +X Tage** (Standard: 7)
   - Webseite analysieren
   - YouTube-Streams erzeugen
   - XML speichern
   - Telegram & Mail-Versand

2. **Heute geplante Streams**:
   - OBS starten & Szene setzen
   - Titel anzeigen
   - RTMP konfigurieren
   - Szenewechsel durchführen
   - Dauerlogik & Telegram-Feedback

3. **Zusammenfassung & Beendigung**

---

## 🔐 Beispiel für Secrets

Siehe vorherige README-Version – gleich geblieben.

---

## 📝 Lizenz

(c) 2025 Andreas Tausch – Pfarrverband Waldkirchen  
Nicht für kommerzielle Nutzung bestimmt. Rückfragen bitte direkt.

---

## ❓ Fragen oder Erweiterungswünsche?

> Für Erweiterungen (z. B. Thumbnail-Handling, PTZ-Kamera-Integration, Stream-Überwachung) bitte Andreas kontaktieren.
---

## 🧹 Wöchentliches Bereinigungs-Skript: `weekly_cleanup_with_telegram.py`

Dieses optionale Zusatzskript löscht automatisch alle YouTube-Videos deines Kanals, die älter als 10 Tage sind.

### 🔁 Ablauf

1. Authentifizierung über bestehendes OAuth2-Token
2. Abfrage aller Videos deines Kanals
3. Löschung von Videos, deren Veröffentlichungsdatum über 10 Tage zurückliegt
4. Versand einer Telegram-Nachricht an **beide Bots** mit Zusammenfassung der gelöschten Videos

### 📤 Beispielnachricht

```
#Bereinigung YouTube
🧹 2 Video(s) gelöscht:
• Sonntag 10:00 – Familienmesse (2025-05-12)
• Mittwoch 19:00 – Maiandacht (2025-05-14)
```

### 🖥️ Ausführung

- Empfohlen: Einmal wöchentlich über Windows Aufgabenplaner (z. B. Sonntag 04:00 Uhr)
- Befehl:
  ```bash
  python weekly_cleanup_with_telegram.py
  ```

### ⚠️ Hinweis

- Nutzt dieselben Zugangsdaten wie `main.py` (`secrets/credentials.json` und `token.json`)
- Logging erfolgt im gleichen Stil wie alle anderen Module