#!/usr/bin/env python3
"""jv-dg-orchestrator — passerelle d'entreprise JARVIS OS (port 9742).

Répond aux routes que les workflows n8n appellent : /health/full, /api/notify,
/api/trading/status, /metrics, /api/memory/remember. Stdlib only, 0 dépendance,
0 token. But immédiat : éteindre les 187/200 erreurs n8n dues au port fantôme.
Lit le registre jv_registry.json pour /health/full.
"""

import json
import re
import sqlite3
import subprocess
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 9742
ROOT = Path.home() / "jarvis"
REGISTRY = ROOT / "orchestrator" / "jv_registry.json"
MEM_DB = ROOT / "db" / "jv_memory.db"
NOTIFY_LOG = ROOT / "logs" / "jv-notify.log"
START = time.time()


def _read_load():
    try:
        with open("/proc/loadavg") as f:
            return [float(x) for x in f.read().split()[:3]]
    except Exception:
        return [0, 0, 0]


def _read_mem():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, v = line.partition(":")
                info[k] = int(v.strip().split()[0])
        total, avail = info.get("MemTotal", 1), info.get("MemAvailable", 0)
        return round(100 * (total - avail) / total, 1)
    except Exception:
        return None


def _gpu():
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        temps = [int(l.split(",")[0]) for l in out.splitlines() if l.strip()]
        return {"count": len(temps), "hottest": max(temps) if temps else None}
    except Exception:
        return {"count": 0, "hottest": None}


def _registry():
    try:
        return json.loads(REGISTRY.read_text())
    except Exception:
        return {"count": 0, "by_dept": {}}


def _mem_db():
    MEM_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(MEM_DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS memory("
        "id INTEGER PRIMARY KEY, ts REAL, category TEXT, payload TEXT)"
    )
    return con


def health_full():
    reg = _registry()
    load = _read_load()
    mem = _read_mem()
    gpu = _gpu()
    degraded = (mem and mem > 90) or load[0] > 12 or (gpu["hottest"] or 0) > 85
    return {
        "status": "degraded" if degraded else "ok",
        "uptime_s": round(time.time() - START),
        "load": load,
        "ram_pct": mem,
        "gpu": gpu,
        "units_total": reg.get("count", 0),
        "departments": {d: len(v) for d, v in reg.get("by_dept", {}).items()},
        "ts": time.time(),
    }


MAX_BODY = 1_000_000  # 1 MiB
# Bind restreint loopback + IP bridge docker (jamais 0.0.0.0 → pas d'exposition LAN physique)
BINDS = ["127.0.0.1", "172.17.0.1"]
# host-allowlist conservée (anti DNS-rebinding) : loopback + passerelle docker
ALLOWED_HOSTS = {
    "127.0.0.1:9742",
    "localhost:9742",
    "127.0.0.1",
    "localhost",
    "host.docker.internal:9742",
    "host.docker.internal",
    "172.17.0.1:9742",
    "172.17.0.1",
}
LEVELS = {"info", "warn", "warning", "error", "debug"}
_CTRL = re.compile(r"[\r\n\x00-\x1f]")


def _clean(s, n=200):
    return _CTRL.sub(" ", str(s))[:n]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _host_ok(self):
        # anti DNS-rebinding / CSRF : Host autorisé + pas d'Origin cross-site
        host = (self.headers.get("Host") or "").lower()
        if host and host not in ALLOWED_HOSTS:
            return False
        origin = self.headers.get("Origin")
        return not origin  # un Origin (requête navigateur cross-site) => refus

    def _send(self, code, obj, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _qs(self):
        return {
            k: v[0]
            for k, v in urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query
            ).items()
        }

    def _route(self):
        return urllib.parse.urlparse(self.path).path

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden host/origin"})
        r = self._route()
        if r in ("/health", "/health/full", "/healthz"):
            return self._send(200, health_full())
        if r == "/api/trading/status":
            return self._send(
                200,
                {
                    "status": "idle",
                    "positions": [],
                    "pnl": 0,
                    "source": "jv-dg-orchestrator",
                    "ts": time.time(),
                },
            )
        if r == "/metrics":
            h = health_full()
            lines = [
                "# JARVIS OS metrics (jv-dg-orchestrator)",
                f"jv_load1 {h['load'][0]}",
                f"jv_ram_pct {h['ram_pct'] or 0}",
                f"jv_gpu_hottest {h['gpu']['hottest'] or 0}",
                f"jv_units_total {h['units_total']}",
                f'jv_status{{state="{h["status"]}"}} 1',
            ]
            return self._send(200, "\n".join(lines).encode(), "text/plain")
        if r == "/api/notify":
            return self._notify(self._qs())
        if r == "/":
            return self._send(
                200,
                {
                    "service": "jv-dg-orchestrator",
                    "port": PORT,
                    "routes": [
                        "/health/full",
                        "/api/notify",
                        "/api/trading/status",
                        "/metrics",
                        "/api/memory/remember",
                    ],
                },
            )
        return self._send(200, {"ok": True, "route": r, "note": "no-op handler"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden host/origin"})
        r = self._route()
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > MAX_BODY:
            return self._send(413, {"error": "payload too large"})
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        data.update(self._qs())
        if r == "/api/notify":
            return self._notify(data)
        if r == "/api/memory/remember":
            try:
                con = _mem_db()
                con.execute(
                    "INSERT INTO memory(ts,category,payload) VALUES(?,?,?)",
                    (
                        time.time(),
                        _clean(data.get("category", "default"), 64),
                        json.dumps(data)[:MAX_BODY],
                    ),
                )
                # budget: ne garder que les 10000 entrées les plus récentes
                con.execute(
                    "DELETE FROM memory WHERE id NOT IN "
                    "(SELECT id FROM memory ORDER BY id DESC LIMIT 10000)"
                )
                con.commit()
                con.close()
                return self._send(200, {"ok": True, "stored": True})
            except Exception as e:
                return self._send(200, {"ok": False, "error": str(e)})
        return self._send(200, {"ok": True, "route": r})

    def _notify(self, data):
        title = _clean(data.get("title", ""))
        msg = _clean(data.get("message", data.get("msg", "")), 500)
        level = data.get("level", "info")
        level = level if level in LEVELS else "info"
        try:
            NOTIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(NOTIFY_LOG, "a") as f:
                f.write(f"{time.strftime('%F %T')} [{level}] {title} :: {msg}\n")
        except Exception:
            pass
        return self._send(200, {"ok": True, "notified": True, "level": level})


if __name__ == "__main__":
    # Bind restreint : loopback (n8n host + local) + IP bridge docker (containers jvnet-*).
    # PAS 0.0.0.0 → non exposé au LAN physique. Host-allowlist = défense en profondeur.
    started = []
    for addr in BINDS:
        try:
            srv = ThreadingHTTPServer((addr, PORT), H)
        except OSError as e:
            print(f"[jv-dg-orchestrator] skip {addr}:{PORT} ({e})")
            continue
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        started.append(addr)
        print(f"[jv-dg-orchestrator] listening on {addr}:{PORT}")
    if not started:
        raise SystemExit("[jv-dg-orchestrator] aucune adresse bindée")
    while True:
        time.sleep(3600)
