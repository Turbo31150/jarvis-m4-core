#!/usr/bin/env python3
"""
jarvis_mcp_http.py — Serveur MCP Streamable-HTTP pour connecter JARVIS à Manus.

Expose http://127.0.0.1:8792/mcp (et /health) selon le protocole
MCP Streamable HTTP (2025-03-26 / 2024-11-05 compatible).

Manus appelle ce serveur via le connecteur "Ajouter MCP par URL"
avec l'URL publique du tunnel Cloudflare.

Outils exposés à Manus :
  • jarvis_ask       — Interroge le cluster LLM JARVIS (lm-ask.sh)
  • jarvis_db_query  — Requête SQLite en lecture seule sur jarvis_master.db
  • jarvis_status    — État des bridges et services JARVIS
  • jarvis_task_log  — Derniers événements Manus dans manus_webhook_events
  • jarvis_shell     — (restreint) Exécute un script JARVIS autorisé

Port : 8792 (distinct du récepteur webhook sur 8791)
Auth : Bearer token lu dans ~/.config/jarvis/manus.env (JARVIS_MCP_TOKEN)
"""

from __future__ import annotations

import json
import os
import shlex
import sqlite3
import subprocess
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
PORT       = int(os.environ.get("JARVIS_MCP_PORT", 8792))
HOST       = "127.0.0.1"
DB         = Path.home() / "jarvis" / "jarvis_master.db"
ENV_FILE   = Path.home() / ".config" / "jarvis" / "manus.env"

def _load_env() -> None:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
MCP_TOKEN = os.environ.get("JARVIS_MCP_TOKEN", "")

# ── Outils MCP ────────────────────────────────────────────────────────────────
TOOLS: list[dict] = [
    {
        "name": "jarvis_ask",
        "description": (
            "Interroge le cluster LLM JARVIS (M1/M2/Ollama). "
            "Utilise lm-ask.sh avec le modèle Qwen ou DeepSeek disponible."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "La question ou consigne à soumettre au LLM local JARVIS"},
                "mode": {"type": "string", "description": "normal | big | reason (défaut: normal)"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "jarvis_db_query",
        "description": "Exécute une requête SELECT en lecture seule sur jarvis_master.db (JARVIS). Accès complet aux tables de logs, tâches, agents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "Requête SELECT SQLite (lecture seule)"},
                "limit": {"type": "integer", "description": "Nombre max de lignes (défaut: 20)"},
            },
            "required": ["sql"],
        },
    },
    {
        "name": "jarvis_status",
        "description": "Retourne l'état en temps réel des bridges, services et ports JARVIS actifs sur M4.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "jarvis_task_log",
        "description": "Derniers événements Manus reçus par JARVIS (via webhook). Retourne les N derniers events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Nombre d'événements (défaut: 10)"},
                "event_type": {"type": "string", "description": "Filtrer par type (ex: task_stopped)"},
            },
        },
    },
]

# ── Handlers ──────────────────────────────────────────────────────────────────
def _tool_jarvis_ask(args: dict) -> str:
    prompt = args.get("prompt", "").strip()
    mode   = args.get("mode", "normal")
    flag   = {"big": "--big", "reason": "--reason"}.get(mode, "")
    cmd    = ["bash", str(Path.home() / "jarvis" / "scripts" / "lm-ask.sh")]
    if flag:
        cmd.append(flag)
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return (r.stdout or r.stderr or "").strip() or "Aucune réponse du LLM."
    except subprocess.TimeoutExpired:
        return "⏱ Timeout LLM JARVIS (120s)"
    except Exception as e:
        return f"❌ Erreur jarvis_ask: {e}"

def _tool_jarvis_db_query(args: dict) -> str:
    sql   = args.get("sql", "").strip()
    limit = min(int(args.get("limit", 20)), 100)
    if not sql.upper().lstrip().startswith("SELECT"):
        return "❌ Seules les requêtes SELECT sont autorisées."
    try:
        conn = sqlite3.connect(str(DB))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchmany(limit)
        conn.close()
        return json.dumps([dict(r) for r in rows], ensure_ascii=False, default=str)
    except Exception as e:
        return f"❌ Erreur SQLite: {e}"

def _tool_jarvis_status(args: dict) -> str:  # noqa: ARG001
    ports = {
        8791: "manus-webhook-receiver",
        8792: "jarvis-mcp-http (ce serveur)",
        9761: "jarvis-web-api",
        8420: "jarvis-monitor",
        18800: "chat_proxy (Telegram→LLM)",
        4173: "lumen-vite-dev",
        3001: "jarvis-lumen-token (docker)",
    }
    results = {}
    for port, name in ports.items():
        cmd = f"curl -sf -m 2 http://127.0.0.1:{port}/ -o /dev/null -w '%{{http_code}}'"
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            code = r.stdout.strip()
            results[name] = f"port {port} → {'🟢 UP' if code in ('200','404','302','401') else '🔴 DOWN'} ({code})"
        except Exception:
            results[name] = f"port {port} → 🔴 DOWN"
    # Tunnel URL
    tunnel_url_file = Path.home() / ".config" / "jarvis" / "manus-tunnel.url"
    results["cloudflare-tunnel"] = tunnel_url_file.read_text().strip() if tunnel_url_file.exists() else "—"
    return json.dumps(results, ensure_ascii=False, indent=2)

def _tool_jarvis_task_log(args: dict) -> str:
    limit      = min(int(args.get("limit", 10)), 50)
    event_type = args.get("event_type", "")
    try:
        conn = sqlite3.connect(str(DB))
        conn.row_factory = sqlite3.Row
        if event_type:
            rows = conn.execute(
                "SELECT received_at,event,task_id,verified,payload FROM manus_webhook_events "
                "WHERE event=? ORDER BY id DESC LIMIT ?",
                (event_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT received_at,event,task_id,verified,payload FROM manus_webhook_events "
                "ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return json.dumps([dict(r) for r in rows], ensure_ascii=False, default=str)
    except Exception as e:
        return f"❌ Erreur SQLite task_log: {e}"

DISPATCH = {
    "jarvis_ask":       _tool_jarvis_ask,
    "jarvis_db_query":  _tool_jarvis_db_query,
    "jarvis_status":    _tool_jarvis_status,
    "jarvis_task_log":  _tool_jarvis_task_log,
}

# ── HTTP Handler ──────────────────────────────────────────────────────────────
class MCPHandler(BaseHTTPRequestHandler):
    def log_message(self, *a, **kw):  # silencieux sauf erreurs
        pass

    def _auth_ok(self) -> bool:
        if not MCP_TOKEN:
            return True  # pas de token configuré → accès ouvert (Cloudflare filtre déjà)
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {MCP_TOKEN}"

    def _send(self, code: int, body: dict | str) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._send(200, {"ok": True, "service": "jarvis-mcp-http", "tools": len(TOOLS)})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self._send(404, {"error": "use POST /mcp"})
            return
        if not self._auth_ok():
            self._send(401, {"error": "Unauthorized"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid JSON"})
            return

        method = msg.get("method", "")
        mid    = msg.get("id")

        if method == "initialize":
            self._send(200, {
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "jarvis-mcp", "version": "1.0.0"},
                },
            })
        elif method == "tools/list":
            self._send(200, {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params  = msg.get("params", {})
            name    = params.get("name", "")
            handler = DISPATCH.get(name)
            if not handler:
                self._send(200, {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32601, "message": f"tool not found: {name}"}})
                return
            try:
                result = handler(params.get("arguments") or {})
            except Exception as e:
                result = f"❌ Exception: {e}"
            self._send(200, {
                "jsonrpc": "2.0", "id": mid,
                "result": {"content": [{"type": "text", "text": result}], "isError": False},
            })
        elif mid is not None:
            self._send(200, {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"method not found: {method}"}})

    do_OPTIONS = do_GET  # CORS preflight simple


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), MCPHandler)
    print(f"🔧 JARVIS MCP HTTP → http://{HOST}:{PORT}/mcp  ({len(TOOLS)} outils)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⛔ Arrêt JARVIS MCP HTTP", flush=True)


if __name__ == "__main__":
    main()
