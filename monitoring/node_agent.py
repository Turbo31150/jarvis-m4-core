#!/usr/bin/env python3
"""
JARVIS Node Agent — expose /metrics on port 8421
Run: python3 node_agent.py [--port 8421]
"""
import argparse
import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

TOOL_COUNTS: dict = {}
TOOL_COUNTS_LOCK = threading.Lock()


def get_cpu_percent() -> float:
    if HAS_PSUTIL:
        return psutil.cpu_percent(interval=0.2)
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        fields = list(map(int, line.split()[1:]))
        idle = fields[3]
        total = sum(fields)
        time.sleep(0.2)
        with open("/proc/stat") as f:
            line = f.readline()
        fields2 = list(map(int, line.split()[1:]))
        idle2 = fields2[3]
        total2 = sum(fields2)
        return round(100.0 * (1 - (idle2 - idle) / (total2 - total)), 1)
    except Exception:
        return -1.0


def get_ram() -> dict:
    if HAS_PSUTIL:
        m = psutil.virtual_memory()
        return {"used_mb": round(m.used / 1024 / 1024), "total_mb": round(m.total / 1024 / 1024), "percent": m.percent}
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.split()[0])
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", 0)
        used = total - avail
        return {"used_mb": round(used / 1024), "total_mb": round(total / 1024), "percent": round(100 * used / total, 1)}
    except Exception:
        return {"used_mb": -1, "total_mb": -1, "percent": -1}


def get_gpus() -> list:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,temperature.gpu,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        gpus = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "temp_c": int(parts[2]) if parts[2].isdigit() else -1,
                    "vram_used_mb": int(parts[3]),
                    "vram_total_mb": int(parts[4]),
                    "util_percent": int(parts[5]) if parts[5].isdigit() else -1
                })
        return gpus
    except Exception:
        return []


def get_services_failed() -> int:
    try:
        r = subprocess.run(
            ["systemctl", "--failed", "--no-legend", "--no-pager"],
            capture_output=True, text=True, timeout=5
        )
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        return len(lines)
    except Exception:
        return -1


def get_lm_status(port: int) -> dict:
    if port is None:
        return {"status": "N/A", "models": []}
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=2) as resp:
            data = json.loads(resp.read())
            models = [m.get("id", "?") for m in data.get("data", [])]
            return {"status": "up", "models": models}
    except Exception:
        return {"status": "down", "models": []}


def get_ollama_status(port: int) -> dict:
    if port is None:
        return {"status": "N/A", "models": []}
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tags", timeout=2) as resp:
            data = json.loads(resp.read())
            models = [m.get("name", "?") for m in data.get("models", [])]
            return {"status": "up", "models": models}
    except Exception:
        return {"status": "down", "models": []}


def get_ping(host: str = "8.8.8.8") -> float:
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "1", host],
                           capture_output=True, text=True, timeout=3)
        for line in r.stdout.splitlines():
            if "time=" in line:
                return float(line.split("time=")[1].split()[0])
        return -1.0
    except Exception:
        return -1.0


class MetricsHandler(BaseHTTPRequestHandler):
    lm_port = None
    ollama_port = None

    def log_message(self, fmt, *args):
        pass  # silent

    def do_GET(self):
        if self.path == "/metrics":
            payload = {
                "ts": time.time(),
                "cpu_percent": get_cpu_percent(),
                "ram": get_ram(),
                "gpus": get_gpus(),
                "services_failed": get_services_failed(),
                "lm_studio": get_lm_status(self.lm_port),
                "ollama": get_ollama_status(self.ollama_port),
                "ping_ms": get_ping(),
                "tool_counts": dict(TOOL_COUNTS)
            }
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


def main():
    parser = argparse.ArgumentParser(description="JARVIS Node Agent")
    parser.add_argument("--port", type=int, default=8421)
    parser.add_argument("--lm-port", type=int, default=None)
    parser.add_argument("--ollama-port", type=int, default=None)
    args = parser.parse_args()

    MetricsHandler.lm_port = args.lm_port
    MetricsHandler.ollama_port = args.ollama_port

    server = HTTPServer(("0.0.0.0", args.port), MetricsHandler)
    print(f"[node_agent] Listening on 0.0.0.0:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[node_agent] Stopped.")


if __name__ == "__main__":
    main()
