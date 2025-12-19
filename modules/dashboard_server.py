import os
from http.server import BaseHTTPRequestHandler
import socketserver

from modules.dashboard_html import HTML_OUTPUT_PATH

PORT = 5000

class CustomHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path in ("/", "/index.html"):
                with open(HTML_OUTPUT_PATH, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "Nicht gefunden")
        except Exception as e:
            self.send_error(500, f"Fehler im Server: {e}")

    def log_message(self, format, *args):
        return

def start_webserver():
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", PORT), CustomHandler)
    return server
