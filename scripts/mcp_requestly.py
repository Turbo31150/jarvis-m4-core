#!/usr/bin/env python3
"""
mcp_requestly.py — MCP Server pour Requestly API Client (filesystem-based)
Lit/écrit directement les fichiers JSON du projet Requestly.

Tools exposés:
  - list_collections     : liste toutes les collections et requests
  - execute_request      : exécute une request par chemin collection/nom
  - add_request          : crée une nouvelle request dans une collection
  - add_collection       : crée une nouvelle collection (dossier)
  - get_request          : lit les détails d'une request
  - delete_request       : supprime une request
  - list_waypoints       : liste les waypoints JARVIS depuis SQLite
  - execute_waypoint     : exécute un waypoint (GET/POST)
  - import_postman       : importe un fichier Postman v2.1 JSON

Usage:
  python3 mcp_requestly.py          # stdio MCP server
  python3 mcp_requestly.py --http   # HTTP server sur :8790
"""

import json
import re
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import httpx
import sys

sys.path.insert(0, "/home/pamerys/IA/Core/jarvis/scripts")
try:
    from jlog import log as _log
except Exception:

    def _log(a, d=None, s="ok"):
        pass


# ── Config ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/home/pamerys/Documents/api request/api")
APIS_ROOT = PROJECT_ROOT / "apis"
DB_PATH = Path("/home/pamerys/IA/Core/jarvis/jarvis_master_index.db")
REQUESTLY_JSON = PROJECT_ROOT / "__requestly.json"

# ── Helpers filesystem ───────────────────────────────────────────────────────


def _safe_name(name: str) -> str:
    """Convertit un nom en nom de dossier safe."""
    return re.sub(r'[<>:"/\\|?*]', "-", name).strip()


def _read_json(path: Path) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _request_dir(collection: str, name: str) -> Path:
    return APIS_ROOT / _safe_name(collection) / _safe_name(name)


# ── Tools ────────────────────────────────────────────────────────────────────


def list_collections() -> dict:
    """Liste toutes les collections et leurs requests."""
    result = {}
    if not APIS_ROOT.exists():
        return {"error": f"APIS_ROOT not found: {APIS_ROOT}"}

    for col_dir in sorted(APIS_ROOT.iterdir()):
        if not col_dir.is_dir() or col_dir.name.startswith("__"):
            continue
        requests = []
        for req_dir in sorted(col_dir.rglob("__metadata.json")):
            meta = _read_json(req_dir)
            if meta:
                rel = req_dir.parent.relative_to(col_dir)
                requests.append(
                    {
                        "name": req_dir.parent.name,
                        "path": str(rel),
                        "method": meta.get("method", "GET"),
                        "url": meta.get("url", ""),
                    }
                )
        result[col_dir.name] = requests
    return result


def get_request(collection: str, name: str) -> dict:
    """Lit les détails complets d'une request."""
    req_dir = _request_dir(collection, name)
    if not req_dir.exists():
        # Cherche en glob
        matches = list(APIS_ROOT.rglob(f"**/{_safe_name(name)}/__metadata.json"))
        if not matches:
            return {"error": f"Request '{name}' not found in '{collection}'"}
        req_dir = matches[0].parent

    meta = _read_json(req_dir / "__metadata.json") or {}
    headers = _read_json(req_dir / "__headers.json") or []
    body = _read_json(req_dir / "__body.json") or {}
    params = _read_json(req_dir / "__query-params.json") or []

    return {
        "name": req_dir.name,
        "url": meta.get("url", ""),
        "method": meta.get("method", "GET"),
        "content_type": meta.get("contentType", "none"),
        "headers": headers,
        "body": body,
        "query_params": params,
    }


def add_request(
    collection: str,
    name: str,
    url: str,
    method: str = "GET",
    headers: list | None = None,
    body: dict | None = None,
    query_params: list | None = None,
) -> dict:
    """Crée une nouvelle request dans une collection."""
    req_dir = _request_dir(collection, name)
    req_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "type": "api",
        "entryType": "http",
        "id": str(uuid.uuid4()),
        "rank": "",
        "url": url,
        "method": method.upper(),
        "contentType": "application/json" if body else "none",
    }
    _write_json(req_dir / "__metadata.json", meta)
    _write_json(req_dir / "__headers.json", headers or [])
    _write_json(req_dir / "__body.json", body or {"contentType": "none"})
    _write_json(req_dir / "__query-params.json", query_params or [])
    _write_json(req_dir / "__auth.json", {"type": "none"})
    _write_json(req_dir / "__path-variables.json", [])

    return {"status": "created", "path": str(req_dir), "url": url, "method": method}


def add_collection(name: str, description: str = "") -> dict:
    """Crée une nouvelle collection (dossier) dans Requestly."""
    col_dir = APIS_ROOT / _safe_name(name)
    col_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        col_dir / "__metadata.json",
        {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
        },
    )
    _write_json(col_dir / "__auth.json", {"type": "none"})
    return {"status": "created", "path": str(col_dir)}


def delete_request(collection: str, name: str) -> dict:
    """Supprime une request."""
    req_dir = _request_dir(collection, name)
    if not req_dir.exists():
        return {"error": f"Not found: {req_dir}"}
    shutil.rmtree(req_dir)
    _log("req_del", {"col": collection, "name": name})
    return {"status": "deleted", "path": str(req_dir)}


def execute_request(
    collection: str,
    name: str,
    timeout: int = 15,
    extra_headers: dict | None = None,
) -> dict:
    """Exécute une request stockée dans Requestly."""
    req = get_request(collection, name)
    if "error" in req:
        return req

    url = req["url"]
    method = req["method"]

    # Headers: liste [{"key":..., "value":...}] → dict
    headers = {h["key"]: h["value"] for h in req["headers"] if h.get("key")}
    if extra_headers:
        headers.update(extra_headers)

    # Query params
    params = {p["key"]: p["value"] for p in req["query_params"] if p.get("key")}

    # Body
    body_data = req.get("body", {})
    json_body = None
    raw_body = None
    if body_data.get("contentType") == "application/json":
        raw = body_data.get("raw", "")
        try:
            json_body = json.loads(raw) if raw else None
        except Exception:
            raw_body = raw

    try:
        resp = httpx.request(
            method,
            url,
            headers=headers,
            params=params or None,
            json=json_body,
            content=raw_body,
            timeout=timeout,
            follow_redirects=True,
        )
        try:
            resp_body = resp.json()
        except Exception:
            resp_body = resp.text[:2000]

        result = {
            "status_code": resp.status_code,
            "url": str(resp.url),
            "method": method,
            "body": resp_body,
            "headers": dict(resp.headers),
        }
        _log("req_exec", {"col": collection, "name": name, "status": resp.status_code})
        return result
    except Exception as e:
        _log("req_exec", {"col": collection, "name": name, "err": str(e)}, "err")
        return {"error": str(e), "url": url, "method": method}


def list_waypoints(limit: int = 50) -> list:
    """Liste les waypoints JARVIS depuis SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT domain, label, url, visit_count FROM nav_waypoints ORDER BY visit_count DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [{"domain": r[0], "label": r[1], "url": r[2], "visits": r[3]} for r in rows]


def execute_waypoint(domain_or_url: str, timeout: int = 10) -> dict:
    """Exécute un GET sur un waypoint par domaine ou URL."""
    url = domain_or_url
    if not url.startswith("http"):
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            row = conn.execute(
                "SELECT url FROM nav_waypoints WHERE domain = ? ORDER BY visit_count DESC LIMIT 1",
                (domain_or_url,),
            ).fetchone()
            conn.close()
            if row:
                url = row[0]
            else:
                url = f"https://{domain_or_url}"

    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        return {
            "status_code": resp.status_code,
            "url": str(resp.url),
            "content_length": len(resp.content),
            "content_type": resp.headers.get("content-type", ""),
        }
    except Exception as e:
        return {"error": str(e), "url": url}


def import_postman(json_path: str) -> dict:
    """Importe un fichier Postman v2.1 dans le filesystem Requestly."""
    path = Path(json_path)
    if not path.exists():
        return {"error": f"File not found: {json_path}"}

    data = json.loads(path.read_text(encoding="utf-8"))

    # Postman v2.1 format
    if "item" in data:
        # Top-level collection
        collection_name = data.get("info", {}).get("name", path.stem)
        return _import_postman_items(
            collection_name, data["item"], APIS_ROOT / _safe_name(collection_name)
        )
    return {"error": "Unknown format — expected Postman v2.1 with 'item' key"}


def _import_postman_items(collection: str, items: list, base_dir: Path) -> dict:
    count = 0
    for item in items:
        if "item" in item:
            # Sub-collection (folder)
            sub_dir = base_dir / _safe_name(item["name"])
            sub_dir.mkdir(parents=True, exist_ok=True)
            _import_postman_items(item["name"], item["item"], sub_dir)
        elif "request" in item:
            req = item["request"]
            name = _safe_name(item["name"])
            req_dir = base_dir / name
            req_dir.mkdir(parents=True, exist_ok=True)

            url_obj = req.get("url", {})
            if isinstance(url_obj, str):
                url = url_obj
                params = []
            else:
                url = url_obj.get("raw", "")
                params = [
                    {
                        "key": p.get("key", ""),
                        "value": p.get("value", ""),
                        "enabled": not p.get("disabled", False),
                    }
                    for p in url_obj.get("query", [])
                ]

            headers = [
                {
                    "key": h["key"],
                    "value": h["value"],
                    "enabled": not h.get("disabled", False),
                }
                for h in req.get("header", [])
            ]

            body_obj = req.get("body", {})
            if body_obj and body_obj.get("mode") == "raw":
                body = {
                    "contentType": "application/json",
                    "raw": body_obj.get("raw", ""),
                }
            else:
                body = {"contentType": "none"}

            meta = {
                "type": "api",
                "entryType": "http",
                "id": str(uuid.uuid4()),
                "rank": "",
                "url": url,
                "method": req.get("method", "GET"),
                "contentType": body.get("contentType", "none"),
            }

            _write_json(req_dir / "__metadata.json", meta)
            _write_json(req_dir / "__headers.json", headers)
            _write_json(req_dir / "__body.json", body)
            _write_json(req_dir / "__query-params.json", params)
            _write_json(req_dir / "__auth.json", {"type": "none"})
            _write_json(req_dir / "__path-variables.json", [])
            count += 1

    return {"status": "imported", "collection": collection, "requests": count}


# ── MCP Server ───────────────────────────────────────────────────────────────

TOOLS = {
    "list_collections": {
        "description": "Liste toutes les collections Requestly et leurs requests",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "fn": lambda args: list_collections(),
    },
    "get_request": {
        "description": "Lit les détails d'une request (URL, method, headers, body)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "description": "Nom de la collection"},
                "name": {"type": "string", "description": "Nom de la request"},
            },
            "required": ["collection", "name"],
        },
        "fn": lambda args: get_request(args["collection"], args["name"]),
    },
    "execute_request": {
        "description": "Exécute une request HTTP stockée dans Requestly",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "name": {"type": "string"},
                "timeout": {"type": "integer", "default": 15},
                "extra_headers": {"type": "object"},
            },
            "required": ["collection", "name"],
        },
        "fn": lambda args: execute_request(
            args["collection"],
            args["name"],
            args.get("timeout", 15),
            args.get("extra_headers"),
        ),
    },
    "add_request": {
        "description": "Ajoute une nouvelle request dans une collection Requestly",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "name": {"type": "string"},
                "url": {"type": "string"},
                "method": {"type": "string", "default": "GET"},
                "headers": {"type": "array"},
                "body": {"type": "object"},
                "query_params": {"type": "array"},
            },
            "required": ["collection", "name", "url"],
        },
        "fn": lambda args: add_request(
            args["collection"],
            args["name"],
            args["url"],
            args.get("method", "GET"),
            args.get("headers"),
            args.get("body"),
            args.get("query_params"),
        ),
    },
    "add_collection": {
        "description": "Crée une nouvelle collection dans Requestly",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string", "default": ""},
            },
            "required": ["name"],
        },
        "fn": lambda args: add_collection(args["name"], args.get("description", "")),
    },
    "delete_request": {
        "description": "Supprime une request de Requestly",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "name": {"type": "string"},
            },
            "required": ["collection", "name"],
        },
        "fn": lambda args: delete_request(args["collection"], args["name"]),
    },
    "list_waypoints": {
        "description": "Liste les waypoints de navigation JARVIS (sites visités)",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 50}},
            "required": [],
        },
        "fn": lambda args: list_waypoints(args.get("limit", 50)),
    },
    "execute_waypoint": {
        "description": "Exécute un GET HTTP sur un waypoint JARVIS par domaine ou URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain_or_url": {
                    "type": "string",
                    "description": "Domaine (ex: linkedin.com) ou URL complète",
                },
                "timeout": {"type": "integer", "default": 10},
            },
            "required": ["domain_or_url"],
        },
        "fn": lambda args: execute_waypoint(
            args["domain_or_url"], args.get("timeout", 10)
        ),
    },
    "import_postman": {
        "description": "Importe un fichier Postman v2.1 JSON dans Requestly (filesystem)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "json_path": {
                    "type": "string",
                    "description": "Chemin absolu vers le fichier JSON",
                }
            },
            "required": ["json_path"],
        },
        "fn": lambda args: import_postman(args["json_path"]),
    },
    "mock_endpoint": {
        "description": "Crée rapidement un endpoint de mock dans Requestly",
        "inputSchema": {
            "type": "object",
            "properties": {
                "collection": {"type": "string", "default": "JARVIS-Mocks"},
                "name": {"type": "string"},
                "url_pattern": {"type": "string", "description": "L'URL à intercepter"},
                "response_body": {"type": "object"},
                "status_code": {"type": "integer", "default": 200}
            },
            "required": ["name", "url_pattern", "response_body"],
        },
        "fn": lambda args: add_request(
            args.get("collection", "JARVIS-Mocks"),
            args["name"],
            args["url_pattern"],
            "GET",
            None,
            {"contentType": "application/json", "raw": json.dumps(args["response_body"])}
        ),
    },
}


def run_stdio():
    """MCP stdio server (JSON-RPC 2.0)."""
    import sys
    import traceback

    def send(obj):
        line = json.dumps(obj, ensure_ascii=False)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method", "")
            req_id = req.get("id")
            params = req.get("params", {})

            if method == "initialize":
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "requestly-jarvis",
                                "version": "1.0.0",
                            },
                        },
                    }
                )

            elif method == "tools/list":
                tools_list = [
                    {
                        "name": name,
                        "description": tool["description"],
                        "inputSchema": tool["inputSchema"],
                    }
                    for name, tool in TOOLS.items()
                ]
                send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}})

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                if tool_name not in TOOLS:
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}",
                            },
                        }
                    )
                else:
                    result = TOOLS[tool_name]["fn"](tool_args)
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": req_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(
                                            result, indent=2, ensure_ascii=False
                                        ),
                                    }
                                ]
                            },
                        }
                    )

            elif method == "notifications/initialized":
                pass  # no response needed

            else:
                send(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown method: {method}",
                        },
                    }
                )

        except Exception as e:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": str(e),
                        "data": traceback.format_exc(),
                    },
                }
            )


def run_http(port: int = 8790):
    """HTTP API server (FastAPI) — alternative au MCP stdio."""
    try:
        from fastapi import FastAPI
        import uvicorn
    except ImportError:
        print("pip install fastapi uvicorn httpx")
        return

    app = FastAPI(title="JARVIS Requestly MCP", version="1.0.0")

    @app.get("/tools")
    def list_tools():
        return [{"name": k, "description": v["description"]} for k, v in TOOLS.items()]

    @app.post("/tools/{tool_name}")
    def call_tool(tool_name: str, args: dict = {}):
        if tool_name not in TOOLS:
            return {"error": f"Tool not found: {tool_name}"}
        return TOOLS[tool_name]["fn"](args)

    @app.get("/collections")
    def api_list_collections():
        return list_collections()

    @app.get("/collections/{collection}")
    def api_get_collection(collection: str):
        cols = list_collections()
        return cols.get(collection, {"error": "not found"})

    @app.post("/collections/{collection}/requests")
    def api_add_request(collection: str, body: dict):
        return add_request(
            collection,
            body.get("name", "unnamed"),
            body.get("url", ""),
            body.get("method", "GET"),
            body.get("headers"),
            body.get("body"),
            body.get("query_params"),
        )

    @app.post("/execute/{collection}/{name}")
    def api_execute(collection: str, name: str, opts: dict = {}):
        return execute_request(
            collection, name, opts.get("timeout", 15), opts.get("headers")
        )

    @app.get("/waypoints")
    def api_waypoints(limit: int = 50):
        return list_waypoints(limit)

    @app.post("/import")
    def api_import(body: dict):
        return import_postman(body.get("path", ""))

    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:
        port = (
            int(sys.argv[sys.argv.index("--http") + 1])
            if len(sys.argv) > sys.argv.index("--http") + 1
            else 8790
        )
        print(f"[REQUESTLY-MCP] HTTP API on http://127.0.0.1:{port}")
        run_http(port)
    else:
        run_stdio()
