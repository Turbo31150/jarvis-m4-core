#!/usr/bin/env python3
"""
JARVIS Cluster Monitor — Central Server
Port 8420
Routes:
  GET  /                      → dashboard.html
  GET  /api/metrics           → all nodes snapshot
  GET  /api/metrics/{node}    → single node
  GET  /api/health            → cluster health summary
  GET  /api/agents            → OpenClaw Docker agents
  GET  /api/agent/{name}/logs → last 20 lines of agent logs
  GET  /api/lm-scores         → LM usage scoring from cowork_engine.db
  WS   /ws                    → push every 3s (nodes + agents + lm_scores)
"""

import asyncio
import json
import logging
import sqlite3
import subprocess
import time
import urllib.request
from datetime import datetime  # noqa: F401 — used in fetch_node crash snapshots
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

CRASH_SNAP_DIR = Path("/home/pamerys/jarvis/logs/crash_snapshots")
CRASH_SNAP_DIR.mkdir(parents=True, exist_ok=True)

# ── Task Metrics ──────────────────────────────────────────────────────────────
_METRICS_MOD = None


def _get_task_metrics():
    global _METRICS_MOD
    if _METRICS_MOD is None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_metrics", Path(__file__).parent / "task_metrics.py"
        )
        _METRICS_MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_METRICS_MOD)
    return _METRICS_MOD


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("jarvis-monitor")

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.json"
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"
COWORK_DB = Path("/home/pamerys/jarvis/cowork_engine.db")

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

NODES = CONFIG["nodes"]
SCRAPE_INTERVAL = CONFIG.get("scrape_interval", 3)

# ── State ─────────────────────────────────────────────────────────────────────
_cache: dict[str, Any] = {}
_agents_cache: list[dict] = []
_lm_scores_cache: list[dict] = []
_ws_clients: list[WebSocket] = []
_node_was_online: dict[str, bool] = {}  # track transitions to avoid snapshot spam

# ── Scraper — nodes ───────────────────────────────────────────────────────────


def fetch_node(node: dict) -> dict:
    name = node["name"]
    host = node["host"]
    port = node["agent_port"]
    url = f"http://{host}:{port}/metrics"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read())
            data["node"] = name
            data["online"] = True
            _node_was_online[name] = True
            return data
    except Exception as e:
        snap = {
            "node": name,
            "online": False,
            "error": str(e),
            "ts": time.time(),
            "ts_human": datetime.now().isoformat(timespec="seconds"),
            "cpu_percent": -1,
            "ram": {"used_mb": -1, "total_mb": -1, "percent": -1},
            "gpus": [],
            "services_failed": -1,
            "lm_studio": {"status": "N/A", "models": []},
            "ollama": {"status": "N/A", "models": []},
            "ping_ms": -1,
            "tool_counts": {},
        }
        prev_online = _node_was_online.get(name, True)
        if prev_online:
            try:
                snap_file = (
                    CRASH_SNAP_DIR
                    / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                snap_file.write_text(json.dumps(snap, indent=2))
            except Exception:
                pass
        _node_was_online[name] = False
        return snap


async def scrape_all() -> dict:
    loop = asyncio.get_event_loop()
    results = {}
    tasks = [loop.run_in_executor(None, fetch_node, node) for node in NODES]
    fetched = await asyncio.gather(*tasks)
    for item in fetched:
        results[item["node"]] = item
    return results


# ── Scraper — Docker agents ───────────────────────────────────────────────────


def fetch_agents() -> list[dict]:
    """Fetch OpenClaw/cowork Docker containers."""
    agents = []
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                "name=openclaw",
                "--filter",
                "name=cowork",
                "--format",
                "{{json .}}",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return [{"_error": "docker_unavailable"}]

        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                state = obj.get("State", "").lower()
                status_icon = (
                    "running"
                    if state == "running"
                    else ("exited" if "exited" in state else "unknown")
                )
                agents.append(
                    {
                        "name": obj.get("Names", ""),
                        "status": state,
                        "status_class": status_icon,
                        "image": obj.get("Image", ""),
                        "uptime": obj.get("Status", ""),
                    }
                )
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        return [{"_error": "docker_not_found"}]
    except subprocess.TimeoutExpired:
        return [{"_error": "docker_timeout"}]
    except Exception as e:
        return [{"_error": str(e)}]
    return agents


def fetch_agent_logs(name: str) -> list[str]:
    """Fetch last 20 log lines of a Docker container."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "20", name],
            capture_output=True,
            text=True,
            timeout=6,
        )
        combined = (result.stdout + result.stderr).strip()
        return combined.splitlines()[-20:]
    except Exception as e:
        return [f"Error: {e}"]


# ── Scraper — LM scores ───────────────────────────────────────────────────────


def fetch_lm_scores() -> list[dict]:
    """Query cowork_engine.db for model usage stats."""
    if not COWORK_DB.exists():
        return []
    try:
        con = sqlite3.connect(str(COWORK_DB), timeout=5)
        con.row_factory = sqlite3.Row
        cur = con.execute("""
            SELECT model, backend,
                   COUNT(*) as calls,
                   AVG(latency_ms) as avg_latency,
                   AVG(quality_score) as avg_score
            FROM model_usage_log
            GROUP BY model, backend
            ORDER BY calls DESC
            LIMIT 20
        """)
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        # Sanitize floats
        for r in rows:
            r["avg_latency"] = round(r["avg_latency"] or 0, 1)
            r["avg_score"] = round(r["avg_score"] or 0, 1)
        return rows
    except Exception as e:
        log.warning(f"LM scores query error: {e}")
        return []


# ── Background loop ───────────────────────────────────────────────────────────


async def scrape_loop():
    global _cache, _agents_cache, _lm_scores_cache
    loop = asyncio.get_event_loop()
    while True:
        try:
            _cache = await scrape_all()
            _agents_cache = await loop.run_in_executor(None, fetch_agents)
            _lm_scores_cache = await loop.run_in_executor(None, fetch_lm_scores)

            payload = json.dumps(
                {
                    "type": "metrics",
                    "data": _cache,
                    "agents": _agents_cache,
                    "lm_scores": _lm_scores_cache,
                    "ts": time.time(),
                }
            )
            dead = []
            for ws in list(_ws_clients):
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                _ws_clients.remove(ws)
        except Exception as e:
            log.error(f"Scrape error: {e}")
        await asyncio.sleep(SCRAPE_INTERVAL)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="JARVIS Cluster Monitor")


@app.on_event("startup")
async def startup():
    asyncio.create_task(scrape_loop())
    log.info("Scraper started")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(DASHBOARD_PATH.read_text())


@app.get("/api/metrics")
async def api_metrics():
    if not _cache:
        data = await scrape_all()
        return JSONResponse(data)
    return JSONResponse(_cache)


@app.get("/api/metrics/{node_name}")
async def api_metrics_node(node_name: str):
    if node_name in _cache:
        return JSONResponse(_cache[node_name])
    node = next((n for n in NODES if n["name"] == node_name), None)
    if not node:
        return JSONResponse({"error": "node not found"}, status_code=404)
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_node, node)
    return JSONResponse(data)


@app.get("/api/health")
async def api_health():
    online = [n for n, d in _cache.items() if d.get("online")]
    offline = [n for n, d in _cache.items() if not d.get("online")]
    total_gpus = sum(len(d.get("gpus", [])) for d in _cache.values() if d.get("online"))
    return JSONResponse(
        {
            "cluster_status": "ok" if offline == [] else "degraded",
            "nodes_online": online,
            "nodes_offline": offline,
            "total_gpus_online": total_gpus,
            "ts": time.time(),
        }
    )


@app.get("/api/agents")
async def api_agents():
    loop = asyncio.get_event_loop()
    agents = await loop.run_in_executor(None, fetch_agents)
    return JSONResponse(agents)


@app.get("/api/agent/{name}/logs")
async def api_agent_logs(name: str):
    loop = asyncio.get_event_loop()
    lines = await loop.run_in_executor(None, fetch_agent_logs, name)
    return JSONResponse({"name": name, "lines": lines})


@app.get("/api/lm-scores")
async def api_lm_scores():
    loop = asyncio.get_event_loop()
    scores = await loop.run_in_executor(None, fetch_lm_scores)
    return JSONResponse(scores)


@app.get("/api/crash-snapshots")
async def api_crash_snapshots(limit: int = 50):
    snaps = sorted(
        CRASH_SNAP_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    result = []
    for p in snaps[:limit]:
        try:
            result.append({"file": p.name, "data": json.loads(p.read_text())})
        except Exception:
            pass
    return JSONResponse({"count": len(result), "snapshots": result})


@app.delete("/api/crash-snapshots")
async def api_clear_snapshots():
    count = 0
    for p in CRASH_SNAP_DIR.glob("*.json"):
        p.unlink()
        count += 1
    return JSONResponse({"deleted": count})


@app.get("/api/task-metrics")
async def api_task_metrics(limit: int = 10):
    loop = asyncio.get_event_loop()
    tm = _get_task_metrics()
    data = await loop.run_in_executor(None, lambda: tm.get_heavy_tasks(limit))
    return JSONResponse(data)


@app.get("/api/task-metrics/{task_id}")
async def api_task_metrics_detail(task_id: int):
    loop = asyncio.get_event_loop()
    tm = _get_task_metrics()
    data = await loop.run_in_executor(None, lambda: tm.get_task_snapshots(task_id))
    if not data:
        return JSONResponse({"error": "task not found"}, status_code=404)
    return JSONResponse(data)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    log.info(f"WS client connected: {websocket.client}")
    if _cache:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "metrics",
                    "data": _cache,
                    "agents": _agents_cache,
                    "lm_scores": _lm_scores_cache,
                    "ts": time.time(),
                }
            )
        )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
        log.info("WS client disconnected")


if __name__ == "__main__":
    port = CONFIG.get("server_port", 8420)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
