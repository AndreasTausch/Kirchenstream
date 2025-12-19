import os
import logging
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, "..", "dashboard_html", "index.html")
os.makedirs(os.path.dirname(HTML_OUTPUT_PATH), exist_ok=True)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<script>
(function() {{
    try {{
        const theme = localStorage.getItem("theme") || "dark";
        document.documentElement.className = theme;
    }} catch (e) {{
        document.documentElement.className = "dark";
    }}
}})();
</script>
<meta http-equiv="refresh" content="10">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    html.dark body {{ background-color: #121212; color: white; }}
    html.light body {{ background-color: #f4f4f4; color: #111; }}
    body {{
        margin: 0; padding: 16px;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        transition: background-color 0.3s, color 0.3s;
    }}
    .row {{ margin-bottom: 10px; padding: 4px; border-bottom: 1px solid #444; }}
    .label {{ font-size: 11px; color: #888; }}
    .status {{ font-weight: 500; font-size: 14px; display: block; margin-top: 2px; }}
    .green {{ color: #4CAF50; }} .yellow {{ color: #FFD700; }}
    .red {{ color: #FF5555; }} .gray {{ color: #888888; }} .white {{ color: #ffffff; }}
    a {{ color: #4FC3F7; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
    .top-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}
    .clock {{ font-size: 12px; }}
    .toggle-btn {{
        padding: 4px 10px;
        font-size: 11px;
        background: #444;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }}
</style>
<script>
    function toggleTheme() {{
        const html = document.documentElement;
        const isDark = html.classList.contains("dark");
        html.classList.toggle("dark", !isDark);
        html.classList.toggle("light", isDark);
        localStorage.setItem("theme", isDark ? "light" : "dark");
    }}
    function updateClock() {{
        const now = new Date();
        const clock = document.getElementById("clock");
        clock.textContent = now.toLocaleTimeString('de-DE');
    }}
    window.onload = function () {{
        const savedTheme = localStorage.getItem("theme") || "dark";
        document.documentElement.classList.add(savedTheme);
        setInterval(updateClock, 1000);
        updateClock();
    }};
</script>
</head>
<body>
<div class="top-bar">
    <button class="toggle-btn" onclick="toggleTheme()">🌓 Darkmode</button>
    <div class="clock" id="clock">⏳</div>
</div>
<div class="row"><span class="label">Titel</span><span class="status">🎬 {title}</span></div>
<div class="row"><span class="label">Datum / Uhrzeit nächster Stream</span><span class="status">📅 {datetime_text}</span></div>
<div class="row"><span class="label">Stream Key</span><span class="status">🗝️ {key}</span></div>
<div class="row"><span class="label">YouTube-Link</span><span class="status">🔗 <a href="{video_url}" target="_blank">{video_url}</a></span></div>
<div class="row"><span class="label">Stream-Status</span><span class="status {status_color}">📡 {status_text}</span></div>
<div class="row"><span class="label">Kamera-Modus</span><span class="status {camera_hint_color}">📷 {camera_hint}</span></div>
<div class="row"><span class="label">Remote-Steuerung</span><span class="status {remote_color}">{remote_text}</span></div>
<div class="row"><span class="label">main.py Status</span><span class="status {main_color}">🧠 {main_status}</span></div>
</body>
</html>
"""

def build_html(title, key, video_url, datetime_text, status_text, status_color,
               camera_hint, camera_hint_color, remote_color, remote_text,
               main_color, main_status):
    try:
        html = HTML_TEMPLATE.format(
            title=title or "-",
            key=key or "-",
            video_url=video_url or "#",
            datetime_text=datetime_text or "-",
            status_text=status_text or "-",
            status_color=status_color or "gray",
            camera_hint=camera_hint or "-",
            camera_hint_color=camera_hint_color or "gray",
            remote_color=remote_color or "gray",
            remote_text=remote_text or "-",
            main_color=main_color or "gray",
            main_status=main_status.replace("\n", "<br>"),
        )

        dir_path = os.path.dirname(HTML_OUTPUT_PATH)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=dir_path, delete=False) as tmp_file:
            tmp_file.write(html)
            temp_name = tmp_file.name

        os.replace(temp_name, HTML_OUTPUT_PATH)

        # Zusätzlich als status.html kopieren
        status_path = os.path.join(os.path.dirname(HTML_OUTPUT_PATH), "status.html")
        try:
            shutil.copy(HTML_OUTPUT_PATH, status_path)
        except Exception as e:
            logging.warning(f"⚠️ Konnte status.html nicht kopieren: {e}")

    except Exception as e:
        logging.error(f"Fehler beim Schreiben der HTML-Datei ({HTML_OUTPUT_PATH})", exc_info=True)