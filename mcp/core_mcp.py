#!/usr/bin/env python3
"""core_mcp.py — Serveur MCP stdio pour les outils natifs de JARVIS OMEGA.

Fournit :
  - linux_exec / system_diagnostics (Shell Linux, santé système, GPU, RAM)
  - docker_ps / docker_restart (Gestion des conteneurs)
  - lmstudio_ask / ollama_ask (Inférence cluster local M1/M2/OL1)
  - gemini_interact (Gemini 3.7 Flash & Interactions API)
  - db_query (Requêtes SQLite JARVIS)
  - git_status (État des dépôts Git JARVIS)
"""

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

PROTOCOL = "2024-11-05"

TOOLS = [
    {
        "name": "linux_exec",
        "description": "Exécute une commande shell Linux sur la machine JARVIS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Ligne de commande shell à exécuter"},
                "cwd": {"type": "string", "description": "Répertoire de travail (défaut /home/pamerys)"},
                "timeout": {"type": "integer", "description": "Timeout en secondes (défaut 60)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "system_diagnostics",
        "description": "Retourne un diagnostic complet du système : CPU, RAM, GPU NVidia, Disque, et bridges réseau JARVIS.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "docker_containers",
        "description": "Liste tous les conteneurs Docker et leur état de santé.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "all": {"type": "boolean", "description": "Inclure conteneurs arrêtés (défaut true)"}
            }
        },
    },
    {
        "name": "lmstudio_ask",
        "description": "Interroge le cluster LLM local JARVIS (M1:10.42.0.230, M2, OL1).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Texte ou consigne pour le LLM"},
                "mode": {"type": "string", "description": "normal | big | reason"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "gemini_interact",
        "description": "Interroge Google Gemini (Interactions API / gemini-3.7-flash / gemini-3.1-pro-preview / antigravity / deep-research).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt ou consigne pour Gemini"},
                "model": {"type": "string", "description": "gemini-3.7-flash | gemini-3.1-pro-preview | gemini-3.5-flash-lite"},
                "agent": {"type": "string", "description": "antigravity-preview-05-2026 | deep-research-preview-04-2026"},
                "previous_id": {"type": "string", "description": "ID d'interaction précédente pour conversation avec contexte"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "db_query",
        "description": "Exécute une requête SQL SELECT sur l'une des bases SQLite de JARVIS (jarvis_master.db, etoile.db, jarvis_logs.db, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "jarvis_master | jarvis_logs | etoile | unified_plan"},
                "sql": {"type": "string", "description": "Requête SELECT SQL"},
                "limit": {"type": "integer", "description": "Limite de résultats (défaut 50)"},
            },
            "required": ["sql"],
        },
    },
]


def handle_linux_exec(args: dict) -> str:
    cmd = args.get("command", "")
    cwd = args.get("cwd", "/home/pamerys")
    timeout = min(int(args.get("timeout", 60)), 300)
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout
        if r.stderr:
            out += "\n[STDERR]\n" + r.stderr
        return out.strip() or f"[Exécuté avec code {r.returncode}, sortie vide]"
    except subprocess.TimeoutExpired:
        return f"⏱ Timeout ({timeout}s) expiré."
    except Exception as e:
        return f"❌ Erreur linux_exec: {e}"


def handle_system_diagnostics(args: dict) -> str:
    diag = {}
    # Mémoire
    try:
        r = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5)
        diag["memory"] = r.stdout.strip()
    except Exception:
        pass

    # Disque
    try:
        r = subprocess.run(["df", "-h", "/", "/storage"], capture_output=True, text=True, timeout=5)
        diag["disk"] = r.stdout.strip()
    except Exception:
        pass

    # GPU
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            diag["gpu"] = r.stdout.strip()
    except Exception:
        pass

    # Bridges & Services
    ports = {
        8792: "jarvis-mcp-http",
        9761: "jarvis-web-api",
        8420: "jarvis-monitor",
        18800: "chat_proxy (Telegram)",
        18810: "omega_gateway",
        1234: "LM Studio (M1 10.42.0.230)",
        11434: "Ollama local",
    }
    services = {}
    for p, name in ports.items():
        if p == 1234:
            host = "10.42.0.230"
        else:
            host = "127.0.0.1"
        cmd = f"curl -sf -m 1 http://{host}:{p}/ -o /dev/null -w '%{{http_code}}'"
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
            code = r.stdout.strip()
            services[f"{name} ({host}:{p})"] = "🟢 UP" if code in ("200", "404", "401", "302", "405") else f"🔴 DOWN ({code})"
        except Exception:
            services[f"{name} ({host}:{p})"] = "🔴 DOWN"
    diag["services"] = services

    return json.dumps(diag, indent=2, ensure_ascii=False)


def handle_docker_containers(args: dict) -> str:
    try:
        r = subprocess.run(["docker", "ps", "-a", "--format", "table {{.Names}}	{{.Status}}	{{.Ports}}"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "Aucun conteneur Docker."
    except Exception as e:
        return f"❌ Erreur Docker: {e}"


def handle_lmstudio_ask(args: dict) -> str:
    prompt = args.get("prompt", "").strip()
    mode = args.get("mode", "normal")
    script = Path("/home/pamerys/jarvis/scripts/lm-ask.sh")
    cmd = ["bash", str(script)]
    if mode == "big":
        cmd.append("--big")
    elif mode == "reason":
        cmd.append("--reason")
    cmd.append(prompt)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return (r.stdout or r.stderr or "").strip() or "Aucune réponse du LLM."
    except subprocess.TimeoutExpired:
        return "⏱ Timeout LLM (120s)"
    except Exception as e:
        return f"❌ Erreur lmstudio_ask: {e}"


def handle_gemini_interact(args: dict) -> str:
    prompt = args.get("prompt", "").strip()
    model = args.get("model", "gemini-3.7-flash")
    agent = args.get("agent")
    prev_id = args.get("previous_id")

    script = Path("/home/pamerys/jarvis/scripts/gemini-interactions.py")
    cmd = ["python3", str(script), "--model", model]
    if agent:
        cmd.extend(["--agent", agent])
    if prev_id:
        cmd.extend(["--prev-id", prev_id])
    cmd.append(prompt)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return (r.stdout or r.stderr or "").strip() or "Aucune réponse de Gemini."
    except subprocess.TimeoutExpired:
        return "⏱ Timeout Gemini (180s)"
    except Exception as e:
        return f"❌ Erreur gemini_interact: {e}"


def handle_db_query(args: dict) -> str:
    db_name = args.get("db_name", "jarvis_master")
    sql = args.get("sql", "").strip()
    limit = min(int(args.get("limit", 50)), 200)

    db_map = {
        "jarvis_master": "/home/pamerys/jarvis/databases/jarvis_master.db",
        "jarvis_logs": "/storage/m1-mirror/databases/jarvis_logs.db",
        "etoile": "/home/pamerys/jarvis/data/etoile.db",
        "unified_plan": "/storage/m1-mirror/databases/unified_plan.db",
        "cowork_engine": "/home/pamerys/jarvis/databases/cowork_engine.db",
    }
    db_path = db_map.get(db_name, db_map["jarvis_master"])
    if not Path(db_path).exists():
        # Fallback local
        db_path = f"/home/pamerys/jarvis/{db_name}.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql)
        rows = cur.fetchmany(limit)
        conn.close()
        return json.dumps([dict(r) for r in rows], indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        return f"❌ Erreur SQLite ({db_name}): {e}"


DISPATCH = {
    "linux_exec": handle_linux_exec,
    "system_diagnostics": handle_system_diagnostics,
    "docker_containers": handle_docker_containers,
    "lmstudio_ask": handle_lmstudio_ask,
    "gemini_interact": handle_gemini_interact,
    "db_query": handle_db_query,
}


def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        mid = req.get("id")
        method = req.get("method")

        if method == "initialize":
            res = {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jarvis-core", "version": "1.0.0"},
            }
            resp = {"jsonrpc": "2.0", "id": mid, "result": res}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name", "")
            args = params.get("arguments") or {}
            handler = DISPATCH.get(name)
            if not handler:
                resp = {
                    "jsonrpc": "2.0",
                    "id": mid,
                    "error": {"code": -32601, "message": f"Tool not found: {name}"},
                }
            else:
                try:
                    result_text = handler(args)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": mid,
                        "result": {"content": [{"type": "text", "text": str(result_text)}], "isError": False},
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": mid,
                        "result": {"content": [{"type": "text", "text": f"Erreur: {e}"}], "isError": True},
                    }
        elif method in ("notifications/initialized", "initialized"):
            continue
        else:
            resp = {
                "jsonrpc": "2.0",
                "id": mid,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
