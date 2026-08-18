#!/usr/bin/env python3
"""Récepteur de webhooks Manus pour JARVIS.

Écoute en local (127.0.0.1:8790 par défaut), vérifie la signature RSA-SHA256
avec la clé publique servie par /v2/webhook.publicKey, journalise chaque
événement dans SQLite, et peut déclencher une chaîne domino.

Rien n'est exposé publiquement par ce script : le tunnel est une étape séparée
et explicite (cloudflared), afin de ne jamais ouvrir n8n ou le LAN par accident.

    python3 manus_webhook_receiver.py [--port 8790] [--host 127.0.0.1]
                                      [--on-event <commande>] [--insecure]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manus_mcp import call  # noqa: E402  (réutilise l'auth + la clé)

DB = Path.home() / "jarvis" / "jarvis_master.db"
KEY_CACHE = Path.home() / ".config" / "jarvis" / "manus-webhook.pub"
SCHEMA = """
CREATE TABLE IF NOT EXISTS manus_webhook_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    received_at TEXT NOT NULL,
    event      TEXT,
    task_id    TEXT,
    verified   INTEGER NOT NULL DEFAULT 0,
    payload    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_manus_wh_task ON manus_webhook_events(task_id);
"""


def public_key() -> bytes | None:
    """Clé publique Manus, mise en cache sur disque."""
    if KEY_CACHE.exists():
        return KEY_CACHE.read_bytes()
    res = call("webhook.publicKey")
    pem = res.get("public_key")
    if not pem:
        print(f"[warn] clé publique indisponible: {res}", file=sys.stderr)
        return None
    KEY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    KEY_CACHE.write_text(pem)
    KEY_CACHE.chmod(0o644)
    return pem.encode()


def verify(
    body: bytes, signature: str, timestamp: str, url: str, pem: bytes | None
) -> tuple[bool, str]:
    """Signature Manus : RSA-SHA256 sur « {timestamp}.{url}.{sha256_hex(body)} ».

    Le header est `X-Webhook-Signature` (base64), horodaté par
    `X-Webhook-Timestamp`. Fenêtre anti-rejeu : 5 minutes.
    """
    if not pem:
        return False, "pas de clé publique"
    if not signature or not timestamp:
        return False, "headers de signature absents"
    try:
        if abs(int(time.time()) - int(timestamp)) > 300:
            return False, "horodatage hors fenêtre (rejeu ?)"
    except ValueError:
        return False, "horodatage illisible"
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        signed = f"{timestamp}.{url}.{hashlib.sha256(body).hexdigest()}".encode()
        key = serialization.load_pem_public_key(pem)
        key.verify(
            base64.b64decode(signature), signed, padding.PKCS1v15(), hashes.SHA256()
        )
        return True, "ok"
    except Exception as exc:
        return False, f"{type(exc).__name__}"


def store(event: str, task_id: str, verified: bool, payload: str) -> int:
    con = sqlite3.connect(DB)
    try:
        con.executescript(SCHEMA)
        cur = con.execute(
            "INSERT INTO manus_webhook_events"
            "(received_at, event, task_id, verified, payload) VALUES (?,?,?,?,?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                event,
                task_id,
                int(verified),
                payload,
            ),
        )
        con.commit()
        return int(cur.lastrowid or 0)
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    pem: bytes | None = None
    on_event: str | None = None
    insecure: bool = False
    public_url: str | None = None  # URL telle qu'enregistrée chez Manus (signée)

    def _reply(self, code: int, msg: str) -> None:
        body = json.dumps({"ok": code < 400, "message": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_mcp(self) -> None:
        """Proxy transparent vers jarvis_mcp_http sur 127.0.0.1:8792."""
        import urllib.request as _ur
        length  = int(self.headers.get("Content-Length") or 0)
        body    = self.rfile.read(length) if length else b""
        verb    = self.command
        dest    = f"http://127.0.0.1:8792{self.path}"
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() in ("content-type", "authorization", "accept")}
        req = _ur.Request(dest, data=body or None, method=verb, headers=headers)
        try:
            with _ur.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            self.send_response(resp.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except Exception as exc:
            err = json.dumps({"ok": False, "error": str(exc)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def do_GET(self) -> None:  # sonde de vie
        if self.path.startswith("/mcp"):
            return self._proxy_mcp()
        self._reply(200, "jarvis manus webhook receiver")

    def do_POST(self) -> None:
        if self.path.startswith("/mcp"):
            return self._proxy_mcp()
        length = int(self.headers.get("Content-Length") or 0)
        if length > 5_000_000:
            return self._reply(413, "payload trop volumineux")
        body = self.rfile.read(length)
        sig = self.headers.get("X-Webhook-Signature") or ""
        ts = self.headers.get("X-Webhook-Timestamp") or ""
        url = self.public_url or f"http://{self.headers.get('Host', '')}{self.path}"
        ok, why = verify(body, sig, ts, url, self.pem)
        if not ok and not self.insecure:
            store(
                f"<signature-rejetée: {why}>",
                "",
                False,
                body[:4000].decode("utf-8", "replace"),
            )
            return self._reply(401, f"signature invalide ({why})")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._reply(400, "json invalide")
        detail = data.get("task_detail") or {}
        event = str(data.get("event_type") or data.get("event") or "")
        task_id = str(detail.get("task_id") or data.get("task_id") or "")
        rid = store(event, task_id, ok, json.dumps(data, ensure_ascii=False))
        print(
            f"[{datetime.now():%H:%M:%S}] #{rid} {event or '?'} task={task_id or '-'} "
            f"{'signé' if ok else 'NON SIGNÉ'}",
            flush=True,
        )
        if self.on_event:
            env = {
                **os.environ,
                "MANUS_EVENT": event,
                "MANUS_TASK_ID": task_id,
                "MANUS_ROW_ID": str(rid),
            }
            subprocess.Popen(
                self.on_event,
                shell=True,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self._reply(200, f"reçu #{rid}")

    def log_message(self, *_args) -> None:  # silence le log par défaut
        return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--on-event", help="commande shell déclenchée à chaque événement")
    ap.add_argument(
        "--public-url",
        help="URL exacte enregistrée chez Manus — elle entre dans la signature",
    )
    ap.add_argument(
        "--insecure",
        action="store_true",
        help="accepte les payloads non signés (tests seulement)",
    )
    args = ap.parse_args()

    Handler.pem = public_key()
    Handler.on_event = args.on_event
    Handler.insecure = args.insecure
    Handler.public_url = args.public_url
    if Handler.pem is None and not args.insecure:
        sys.exit("clé publique introuvable — relance avec --insecure pour tester")

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(
        f"récepteur Manus sur http://{args.host}:{args.port} "
        f"(signature {'vérifiée' if Handler.pem else 'DÉSACTIVÉE'}) · base {DB}",
        flush=True,
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
