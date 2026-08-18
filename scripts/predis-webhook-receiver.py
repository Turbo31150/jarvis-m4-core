#!/usr/bin/env python3
"""Récepteur webhook Predis.ai — persiste les notifs de fin de génération.
Predis POST ici quand un post est prêt → on log + auto-download des médias.
Écoute 0.0.0.0:18877 (exposé via cloudflared quick tunnel).
"""

import json
import os
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PREDIS_WEBHOOK_PORT", "18877"))
CFG = os.path.expanduser("~/.config/predis")
LOG = os.path.join(CFG, "webhook_log.jsonl")
MEDIA_DIR = os.path.expanduser("~/jarvis/data/predis_media")
os.makedirs(MEDIA_DIR, exist_ok=True)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _download_media(payload):
    """Best-effort: télécharge toute URL média trouvée dans le payload."""
    saved = []
    urls = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif (
            isinstance(o, str)
            and o.startswith("http")
            and any(
                o.lower().split("?")[0].endswith(ext)
                for ext in (".png", ".jpg", ".jpeg", ".mp4", ".gif", ".webp")
            )
        ):
            urls.append(o)

    walk(payload)
    for u in urls:
        try:
            name = u.split("?")[0].split("/")[-1]
            dest = os.path.join(MEDIA_DIR, f"{int(datetime.now().timestamp())}_{name}")
            urllib.request.urlretrieve(u, dest)
            saved.append(dest)
        except Exception as e:  # noqa: BLE001
            saved.append(f"ERR {u}: {e}")
    return saved


class Handler(BaseHTTPRequestHandler):
    def _ok(self, body=b'{"status":"received"}'):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # healthcheck / validation Predis
        self._ok(b'{"status":"ok","service":"predis-webhook"}')

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:  # noqa: BLE001
            payload = {"_raw": raw.decode(errors="replace")}
        media = _download_media(payload)
        rec = {
            "ts": _now(),
            "path": self.path,
            "payload": payload,
            "media_saved": media,
        }
        with open(LOG, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[{rec['ts']}] webhook hit — media: {len(media)}", flush=True)
        self._ok()

    def log_message(self, *a):  # silence default stderr noise
        pass


if __name__ == "__main__":
    print(f"Predis webhook receiver on :{PORT} → log {LOG}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
