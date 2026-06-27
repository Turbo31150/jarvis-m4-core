#!/usr/bin/env python3
"""Bridge 9742 → JARVIS Whisper 9743 (WhisperFlow-compatible API)"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, sys

TARGET = "http://127.0.0.1:9743"

class Bridge(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        ct = self.headers.get("Content-Type", "")
        try:
            req = urllib.request.Request(TARGET + self.path, data=body,
                headers={"Content-Type": ct, "Content-Length": str(len(body))},
                method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                self.send_response(200)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        try:
            req = urllib.request.Request(TARGET + self.path)
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read()
                self.send_response(200)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "bridge": "9742->9743"}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

print("WhisperFlow bridge 9742 → 9743 started")
HTTPServer(("127.0.0.1", 9742), Bridge).serve_forever()
